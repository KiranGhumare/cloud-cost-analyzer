import boto3
import datetime
from typing import Any

UNDERUTILISED_CPU_THRESHOLD = 10.0
LOOKBACK_DAYS = 14
METRIC_PERIOD = 86400 

def get_ec2_client(region: str = "us-east-1") -> Any:
    return boto3.client("ec2", region_name=region)

def get_cloudwatch_client(region: str = "us-east-1") -> Any:
    return boto3.client("cloudwatch", region_name=region)

def fetch_running_instances(region: str = "us-east-1") -> list[dict]:
    ec2 = get_ec2_client(region)
    response = ec2.describe_instances(
        Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
    )

    instances = []
    for reservation in response.get("Reservations", []):
        for instance in reservation.get("Instances", []):
            name = ""
            for tag in instance.get("Tags", []):
                if tag["Key"] == "Name":
                    name = tag["Value"]

            instances.append({
                "instance_id": instance["InstanceId"],
                "instance_type": instance["InstanceType"],
                "launch_time": instance["LaunchTime"].isoformat(),
                "name": name,
                "region": region,
            })

    return instances

def fetch_cpu_utilisation(instance_id: str, region: str = "us-east-1") -> float | None:
    cw = get_cloudwatch_client(region)
    end_time = datetime.datetime.now(datetime.timezone.utc)
    start_time = end_time- datetime.timedelta(days=LOOKBACK_DAYS)

    response = cw.get_metric_statistics(
        Namespace = "AWS/EC2",
        MetricName = "CPUUtilization",
        Dimensions = [{"Name": "InstanceId", "Value": instance_id}],
        StartTime = start_time,
        EndTime = end_time,
        Period= METRIC_PERIOD,
        Statistics = ["Average"],
    )

    datapoints = response.get("Datapoints", [])
    if not datapoints:
        return None
    
    avg_cpu = sum(d["Average"] for d in datapoints)/len(datapoints)
    return round(avg_cpu, 2)

def collect_underutilised_ec2(region: str = "us-east-1") -> list[dict]:
    instances = fetch_running_instances(region)
    underutilised = []

    for instance in instances:
        avg_cpu = fetch_cpu_utilisation(instance["instance_id"], region)
        if avg_cpu is None:
            continue

        instance["avg_cpu_percent"] = avg_cpu
        instance["lookback_days"] = LOOKBACK_DAYS

        if avg_cpu < UNDERUTILISED_CPU_THRESHOLD:
            instance["flag"] = "underutilised"
            underutilised.append(instance)

    return underutilised


EC2_TOOL_DEFINITION = {
    "name": "get_underutilised_ec2",
    "description": (
        "Fetch all running EC2 instances with average CPU utilisation below 10% "
        "over the last 14 days. Use this when analysing compute waste."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "region": {
                "type": "string",
                "description": "AWS region to scan. Defaults to us-east-1.",
                "default": "us-east-1",
            }
        },
        "required": [],
    }
}
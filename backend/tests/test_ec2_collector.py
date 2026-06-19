import datetime
import boto3
import pytest
from moto import mock_aws
from backend.collectors.ec2_collector import (
    fetch_running_instances,
    fetch_cpu_utilisation,
    collect_underutilised_ec2,
    UNDERUTILISED_CPU_THRESHOLD,
    LOOKBACK_DAYS,
)

REGION = "us-east-1"
FAKE_AMI = "ami-12345678"

def seed_ec2_instance(instance_type: str = "m5.2xlarge") -> str:
    ec2 = boto3.client("ec2", region_name=REGION)
    response = ec2.run_instances(
        ImageId=FAKE_AMI,
        MinCount=1,
        MaxCount=1,
        InstanceType=instance_type,
        TagSpecifications=[{
            "ResourceType": "instance",
            "Tags": [{"Key": "Name", "Value": "test-instance"}],
        }],
    )
    return response["Instances"][0]["InstanceId"]

def seed_cpu_metric(instance_id: str, avg_cpu: float) -> None:
    cw = boto3.client("cloudwatch", region_name=REGION)
    now = datetime.datetime.now(datetime.timezone.utc)

    for day in range(LOOKBACK_DAYS):
        timestamp = now - datetime.timedelta(days=day + 1)
        cw.put_metric_data(
            Namespace="AWS/EC2",
            MetricData=[{
                "MetricName": "CPUUtilization",
                "Dimensions": [{"Name": "InstanceId", "Value": instance_id}],
                "Timestamp": timestamp,
                "Value": avg_cpu,
                "Unit": "Percent",
            }],
        )

@mock_aws
def test_fetch_running_instances_returns_list():
    seed_ec2_instance()
    instances = fetch_running_instances(REGION)
    assert isinstance(instances, list)
    assert len(instances) == 1
    assert "instance_id" in instances[0]
    assert "instance_type" in instances[0]

@mock_aws
def test_fetch_running_instances_empty_when_none():
    instances = fetch_running_instances(REGION)
    assert instances == []

@mock_aws
def test_fetch_cpu_returns_none_with_no_datapoints():
    instance_id = seed_ec2_instance()
    result = fetch_cpu_utilisation(instance_id, REGION)
    assert result is None

@mock_aws
def test_fetch_cpu_returns_correct_average():
    import datetime
    instance_id = seed_ec2_instance()
    seed_cpu_metric(instance_id, avg_cpu=3.5)
    
    # Debug — check what CloudWatch actually has
    cw = boto3.client("cloudwatch", region_name=REGION)
    now = datetime.datetime.now(datetime.timezone.utc)
    response = cw.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
        StartTime=now - datetime.timedelta(days=15),
        EndTime=now,
        Period=86400,
        Statistics=["Average"],
    )
    print("\nDatapoints found:", response["Datapoints"])
    
    result = fetch_cpu_utilisation(instance_id, REGION)
    assert result is not None
    assert abs(result - 3.5) < 0.5

@mock_aws
def test_collect_flags_underutilised_instance():
    instance_id = seed_ec2_instance("m5.2xlarge")
    seed_cpu_metric(instance_id, avg_cpu=3.2)

    results = collect_underutilised_ec2(REGION)

    assert len(results) == 1
    assert results[0]["instance_id"] == instance_id
    assert results[0]["flag"] == "underutilised"
    assert results[0]["avg_cpu_percent"] < UNDERUTILISED_CPU_THRESHOLD

@mock_aws
def test_collect_does_not_flag_healthy_instance():
    instance_id = seed_ec2_instance("t3.micro")
    seed_cpu_metric(instance_id, avg_cpu=45.0)

    results = collect_underutilised_ec2(REGION)
    assert results == []

@mock_aws
def test_collect_mixed_instances():
    id_idle = seed_ec2_instance("m5.2xlarge")
    id_busy = seed_ec2_instance("t3.large")

    seed_cpu_metric(id_idle, avg_cpu=2.1)
    seed_cpu_metric(id_busy, avg_cpu=62.0)

    results = collect_underutilised_ec2(REGION)

    assert len(results) == 1
    assert results[0]["instance_id"] == id_idle

@mock_aws
def test_collect_skips_instance_with_no_metrics():
    seed_ec2_instance("c5.xlarge")
    results = collect_underutilised_ec2(REGION)
    assert results == []
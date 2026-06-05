from datetime import datetime, timedelta, timezone
from typing import Any

_IDLE_CPU_THRESHOLD = 5.0  # percent
_LOOKBACK_DAYS = 14


def find_idle_ec2_instances(ec2_client, cw_client) -> list[dict[str, Any]]:
    """Return running EC2 instances whose average CPU < 5% over the past 14 days."""
    instances: list[dict] = []
    paginator = ec2_client.get_paginator("describe_instances")

    for page in paginator.paginate(
        Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
    ):
        for reservation in page["Reservations"]:
            instances.extend(reservation["Instances"])

    now = datetime.now(timezone.utc)
    lookback = now - timedelta(days=_LOOKBACK_DAYS)
    findings: list[dict[str, Any]] = []

    for inst in instances:
        instance_id = inst["InstanceId"]
        resp = cw_client.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
            StartTime=lookback,
            EndTime=now,
            Period=86400,
            Statistics=["Average"],
        )
        datapoints = resp.get("Datapoints", [])
        if not datapoints:
            continue

        avg_cpu = sum(d["Average"] for d in datapoints) / len(datapoints)
        if avg_cpu >= _IDLE_CPU_THRESHOLD:
            continue

        name = next(
            (t["Value"] for t in inst.get("Tags", []) if t["Key"] == "Name"),
            instance_id,
        )
        findings.append(
            {
                "instance_id": instance_id,
                "name": name,
                "instance_type": inst["InstanceType"],
                "avg_cpu_percent_14d": round(avg_cpu, 2),
                "launch_time": inst["LaunchTime"].isoformat(),
                "availability_zone": inst["Placement"]["AvailabilityZone"],
            }
        )

    return findings

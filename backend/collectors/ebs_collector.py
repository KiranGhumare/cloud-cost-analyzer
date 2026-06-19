import boto3
from typing import Any

def calculate_ebs_monthly_cost(size_gb: int, volume_type: str) -> float:
    prices = {
        "gp2": 0.10,
        "gp3": 0.08,
        "io1": 0.125,
    }
    price_per_gb = prices.get(volume_type, 0.10)
    return round(size_gb * price_per_gb, 2)

def get_ec2_client(region: str = "us-east-1") -> Any:
    return boto3.client("ec2", region_name=region)


def fetch_unattached_volumes(region: str = "us-east-1") -> list[dict]:
    ec2 = get_ec2_client(region)
    response = ec2.describe_volumes(
        Filters=[{"Name": "status", "Values": ["available"]}]
    )

    volumes = []
    for volume in response.get("Volumes", []):
        volumes.append({
            "volume_id": volume["VolumeId"],
            "size_gb": volume["Size"],
            "volume_type": volume["VolumeType"],
            "state": "available",
            "availability_zone": volume["AvailabilityZone"],
            "estimated_monthly_cost_usd": calculate_ebs_monthly_cost(volume["Size"], volume["VolumeType"]),
            "region": region
        })

    return volumes

def fetch_unused_elastic_ips(region: str = "us-east-1") -> list[dict]:
    ec2 = get_ec2_client(region)
    response = ec2.describe_addresses()

    unused_elastic_ips = []
    for address in response["Addresses"]:
        if "InstanceId" not in address:
            unused_elastic_ips.append({
                "public_ip": address["PublicIp"],
                "allocation_id": address["AllocationId"],
                "region": region
            })

    return unused_elastic_ips

def collect_ebs_and_elastic_ip_waste(region: str = "us-east-1") -> list[dict]:
    unattached_volumes = fetch_unattached_volumes(region)
    elastic_ips = fetch_unused_elastic_ips(region)

    for volume in unattached_volumes:
        volume["flag"] = "unattached_volume"

    for ip in elastic_ips:
        ip["flag"] = "unused_elastic_ip"

    return unattached_volumes + elastic_ips
    

EBS_ELASTIC_IP_TOOL_DEFINITION = {
    "name": "get_ebs_and_elastic_ip_waste",
    "description":(
        "Fetch all unattached EBS volumes and unused Elastic IPs in an AWS account. "
        "Unattached EBS volumes are paying for storage attached to nothing. "
        "Unused Elastic IPs incur hourly charges when not associated with a running instance. "
        "Use this when analysing storage and networking waste."
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
    },
}
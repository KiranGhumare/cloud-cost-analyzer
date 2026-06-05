from typing import Any

# USD per GB per month — us-east-1 pricing as of 2025
_PRICE_PER_GB: dict[str, float] = {
    "gp2": 0.10,
    "gp3": 0.08,
    "io1": 0.125,
    "io2": 0.125,
    "st1": 0.045,
    "sc1": 0.025,
    "standard": 0.05,
}


def find_unattached_ebs_volumes(ec2_client) -> list[dict[str, Any]]:
    """Return EBS volumes in 'available' state (not attached to any instance)."""
    paginator = ec2_client.get_paginator("describe_volumes")
    findings: list[dict[str, Any]] = []

    for page in paginator.paginate(Filters=[{"Name": "status", "Values": ["available"]}]):
        for vol in page["Volumes"]:
            vol_type = vol["VolumeType"]
            size_gb = vol["Size"]
            price = _PRICE_PER_GB.get(vol_type, 0.10)
            findings.append(
                {
                    "volume_id": vol["VolumeId"],
                    "size_gb": size_gb,
                    "volume_type": vol_type,
                    "state": vol["State"],
                    "availability_zone": vol["AvailabilityZone"],
                    "estimated_monthly_cost_usd": round(price * size_gb, 2),
                }
            )

    return findings

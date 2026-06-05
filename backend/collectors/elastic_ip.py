from typing import Any

_HOURLY_COST_USD = 0.005
_HOURS_PER_MONTH = 730


def find_unattached_elastic_ips(ec2_client) -> list[dict[str, Any]]:
    """Return Elastic IPs that are not associated with any instance or network interface."""
    resp = ec2_client.describe_addresses()
    findings: list[dict[str, Any]] = []

    for addr in resp.get("Addresses", []):
        if not addr.get("AssociationId"):
            findings.append(
                {
                    "allocation_id": addr.get("AllocationId", ""),
                    "public_ip": addr["PublicIp"],
                    "domain": addr.get("Domain", "vpc"),
                    "estimated_monthly_cost_usd": round(_HOURLY_COST_USD * _HOURS_PER_MONTH, 2),
                }
            )

    return findings

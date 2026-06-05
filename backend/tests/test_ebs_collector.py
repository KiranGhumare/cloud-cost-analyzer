import boto3
import pytest
from moto import mock_aws

from backend.collectors.ebs import find_unattached_ebs_volumes


# ── helpers ──────────────────────────────────────────────────────────────────

def create_attached_volume(ec2_client, ec2_resource):
    """Creates an EC2 instance and attaches a volume to it."""
    # Need a real AMI-like setup — moto provides a default AMI
    instance = ec2_resource.create_instances(
        ImageId="ami-12345678",
        MinCount=1,
        MaxCount=1,
        BlockDeviceMappings=[
            {
                "DeviceName": "/dev/xvda",
                "Ebs": {"VolumeSize": 20, "DeleteOnTermination": False},
            }
        ],
    )[0]
    return instance


def create_unattached_volume(ec2_client, size_gb=100, volume_type="gp2"):
    """Creates a standalone volume with no attachment."""
    volume = ec2_client.create_volume(
        AvailabilityZone="us-east-1a",
        Size=size_gb,
        VolumeType=volume_type,
    )
    return volume


# ── tests ─────────────────────────────────────────────────────────────────────

@mock_aws
class TestUnattachedEBSCollector:

    def setup_method(self, method=None):
        """Runs before each test — fresh boto3 clients inside the mock."""
        self.ec2_client = boto3.client("ec2", region_name="us-east-1")
        self.ec2_resource = boto3.resource("ec2", region_name="us-east-1")

    def test_detects_single_unattached_volume(self):
        """A single unattached volume should be returned as a finding."""
        create_unattached_volume(self.ec2_client, size_gb=100)

        findings = find_unattached_ebs_volumes(self.ec2_client)

        assert len(findings) == 1
        assert findings[0]["state"] == "available"
        assert findings[0]["size_gb"] == 100

    def test_ignores_attached_volumes(self):
        """Volumes attached to an instance should not appear in findings."""
        create_attached_volume(self.ec2_client, self.ec2_resource)

        findings = find_unattached_ebs_volumes(self.ec2_client)

        # Root volume is attached — should not be flagged
        assert len(findings) == 0

    def test_mixed_volumes_only_returns_unattached(self):
        """Only unattached volumes returned when both types exist."""
        create_attached_volume(self.ec2_client, self.ec2_resource)
        create_unattached_volume(self.ec2_client, size_gb=50)
        create_unattached_volume(self.ec2_client, size_gb=200)

        findings = find_unattached_ebs_volumes(self.ec2_client)

        assert len(findings) == 2
        sizes = {f["size_gb"] for f in findings}
        assert sizes == {50, 200}

    def test_returns_empty_when_no_volumes(self):
        """No volumes in account should return empty list, not an error."""
        findings = find_unattached_ebs_volumes(self.ec2_client)

        assert findings == []

    def test_finding_contains_required_fields(self):
        """Each finding must have the fields the AI agent needs to reason over."""
        create_unattached_volume(self.ec2_client, size_gb=100, volume_type="gp2")

        findings = find_unattached_ebs_volumes(self.ec2_client)

        assert len(findings) == 1
        finding = findings[0]

        # Fields the agent needs
        assert "volume_id" in finding
        assert "size_gb" in finding
        assert "volume_type" in finding
        assert "state" in finding
        assert "availability_zone" in finding
        assert "estimated_monthly_cost_usd" in finding

    def test_estimates_monthly_cost(self):
        """gp2 costs $0.10/GB/month — 100GB volume = $10/month."""
        create_unattached_volume(self.ec2_client, size_gb=100, volume_type="gp2")

        findings = find_unattached_ebs_volumes(self.ec2_client)

        assert findings[0]["estimated_monthly_cost_usd"] == pytest.approx(10.0)

    def test_multiple_volume_types(self):
        """Cost estimate should reflect volume type (gp3 vs gp2 vs io1)."""
        create_unattached_volume(self.ec2_client, size_gb=100, volume_type="gp2")
        create_unattached_volume(self.ec2_client, size_gb=100, volume_type="gp3")

        findings = find_unattached_ebs_volumes(self.ec2_client)
        by_type = {f["volume_type"]: f for f in findings}

        # gp2 = $0.10/GB, gp3 = $0.08/GB
        assert by_type["gp2"]["estimated_monthly_cost_usd"] == pytest.approx(10.0)
        assert by_type["gp3"]["estimated_monthly_cost_usd"] == pytest.approx(8.0)
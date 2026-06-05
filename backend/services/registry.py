from dataclasses import dataclass, field


@dataclass
class ServiceDefinition:
    id: str
    name: str
    description: str
    iam_actions: list[str]
    supported: bool = True


_REGISTRY: dict[str, ServiceDefinition] = {
    "ebs": ServiceDefinition(
        id="ebs",
        name="EBS Volumes",
        description="Detects unattached EBS volumes incurring storage costs with no utilisation.",
        iam_actions=["ec2:DescribeVolumes"],
    ),
    "ec2": ServiceDefinition(
        id="ec2",
        name="EC2 Instances",
        description="Flags idle EC2 instances with consistently low CPU utilisation over 14 days.",
        iam_actions=[
            "ec2:DescribeInstances",
            "cloudwatch:GetMetricStatistics",
            "cloudwatch:GetMetricData",
        ],
    ),
    "elastic_ip": ServiceDefinition(
        id="elastic_ip",
        name="Elastic IPs",
        description="Finds Elastic IPs not associated with a running instance ($0.005/hr idle charge).",
        iam_actions=["ec2:DescribeAddresses"],
    ),
    "s3": ServiceDefinition(
        id="s3",
        name="S3 Buckets",
        description="Identifies buckets missing lifecycle policies or using suboptimal storage classes.",
        iam_actions=[
            "s3:ListAllMyBuckets",
            "s3:GetBucketLocation",
            "s3:GetBucketLifecycleConfiguration",
            "s3:GetBucketStorageClassAnalysis",
        ],
        supported=False,
    ),
    "rds": ServiceDefinition(
        id="rds",
        name="RDS Instances",
        description="Identifies idle or oversized RDS instances based on connection and CPU metrics.",
        iam_actions=[
            "rds:DescribeDBInstances",
            "cloudwatch:GetMetricStatistics",
        ],
        supported=False,
    ),
    "lambda": ServiceDefinition(
        id="lambda",
        name="Lambda Functions",
        description="Flags Lambda functions with over-provisioned memory relative to actual usage.",
        iam_actions=[
            "lambda:ListFunctions",
            "lambda:GetFunctionConfiguration",
            "cloudwatch:GetMetricStatistics",
        ],
        supported=False,
    ),
}


def list_services() -> list[ServiceDefinition]:
    return list(_REGISTRY.values())


def get_service(service_id: str) -> ServiceDefinition | None:
    return _REGISTRY.get(service_id)

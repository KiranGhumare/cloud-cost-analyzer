from .registry import get_service

# Always included — needed to correlate telemetry with billing
_BASE_ACTIONS = [
    "ce:GetCostAndUsage",
    "ce:GetCostForecast",
]


def generate_iam_policy(service_ids: list[str]) -> dict:
    """Return a minimal read-only IAM policy document for the given services."""
    actions: set[str] = set(_BASE_ACTIONS)

    for sid in service_ids:
        svc = get_service(sid)
        if svc:
            actions.update(svc.iam_actions)

    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "CloudCostAnalyserReadOnly",
                "Effect": "Allow",
                "Action": sorted(actions),
                "Resource": "*",
            }
        ],
    }

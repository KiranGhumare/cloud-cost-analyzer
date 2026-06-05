from fastapi import APIRouter

from ..models.schemas import IAMPolicyRequest, IAMPolicyResponse, ServiceInfo
from ..services.iam_policy import generate_iam_policy
from ..services.registry import list_services

router = APIRouter(prefix="/api/services", tags=["services"])


@router.get("", response_model=list[ServiceInfo])
async def get_services():
    return [
        ServiceInfo(
            id=s.id,
            name=s.name,
            description=s.description,
            supported=s.supported,
        )
        for s in list_services()
    ]


@router.post("/iam-policy", response_model=IAMPolicyResponse)
async def get_iam_policy(body: IAMPolicyRequest):
    """Generate a minimal read-only IAM policy for the selected services."""
    policy = generate_iam_policy(body.service_ids)
    return IAMPolicyResponse(policy=policy, service_ids=body.service_ids)

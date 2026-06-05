import asyncio
import uuid
from datetime import datetime, timezone

import boto3
from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from ..analysers import get_provider
from ..collectors.ebs import find_unattached_ebs_volumes
from ..collectors.ec2 import find_idle_ec2_instances
from ..collectors.elastic_ip import find_unattached_elastic_ips
from ..config import settings
from ..database import get_session
from ..models.db import AnalysisRun, Finding
from ..models.schemas import (
    AnalysisReport,
    AnalysisRequest,
    FindingActionRequest,
)

router = APIRouter(prefix="/api", tags=["analysis"])

# Maps service id → coroutine factory that accepts the boto3 clients dict
_COLLECTORS = {
    "ebs": lambda c: asyncio.to_thread(find_unattached_ebs_volumes, c["ec2"]),
    "ec2": lambda c: asyncio.to_thread(find_idle_ec2_instances, c["ec2"], c["cloudwatch"]),
    "elastic_ip": lambda c: asyncio.to_thread(find_unattached_elastic_ips, c["ec2"]),
}


def _boto3_clients(region: str) -> dict:
    session = boto3.Session(
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=region,
    )
    return {
        "ec2": session.client("ec2"),
        "cloudwatch": session.client("cloudwatch"),
    }


@router.post("/analyze", response_model=AnalysisReport)
async def run_analysis(body: AnalysisRequest):
    runnable = [s for s in body.service_ids if s in _COLLECTORS]
    if not runnable:
        raise HTTPException(
            status_code=400,
            detail=f"No supported services in {body.service_ids}. Supported: {list(_COLLECTORS)}",
        )

    clients = _boto3_clients(settings.aws_default_region)
    telemetry: dict = {}

    for svc_id in runnable:
        try:
            telemetry[svc_id] = await _COLLECTORS[svc_id](clients)
        except Exception as exc:
            telemetry[svc_id] = {"error": str(exc)}

    _api_keys = {
        "anthropic": settings.anthropic_api_key,
        "gemini": settings.gemini_api_key,
        "openai": settings.openai_api_key,
    }
    api_key = _api_keys.get(body.llm_provider, "")
    provider = get_provider(body.llm_provider, api_key)
    findings = await provider.generate_findings(telemetry)

    run_id = uuid.uuid4()
    total_savings = sum(f.estimated_monthly_savings_usd for f in findings)

    async with get_session() as session:
        run = AnalysisRun(
            id=run_id,
            services=runnable,
            total_savings_usd=total_savings,
            llm_provider=body.llm_provider,
        )
        session.add(run)
        for f in findings:
            session.add(
                Finding(
                    run_id=run_id,
                    service=f.service,
                    resource_id=f.resource_id,
                    resource_type=f.resource_type,
                    finding_type=f.finding_type,
                    description=f.description,
                    estimated_monthly_savings_usd=f.estimated_monthly_savings_usd,
                    confidence=f.confidence,
                    recommendation=f.recommendation,
                    finding_metadata=f.metadata,
                )
            )

    return AnalysisReport(
        run_id=run_id,
        timestamp=datetime.now(timezone.utc),
        services_analyzed=runnable,
        total_estimated_savings_usd=total_savings,
        findings=findings,
        llm_provider=body.llm_provider,
    )


@router.get("/analyses", response_model=list[dict])
async def list_analyses():
    async with get_session() as session:
        result = await session.execute(
            select(AnalysisRun).order_by(AnalysisRun.created_at.desc()).limit(20)
        )
        runs = result.scalars().all()

    return [
        {
            "id": str(r.id),
            "created_at": r.created_at.isoformat(),
            "services": r.services,
            "total_savings_usd": r.total_savings_usd,
            "llm_provider": r.llm_provider,
        }
        for r in runs
    ]


@router.patch("/findings/{finding_id}/action")
async def action_finding(finding_id: str, body: FindingActionRequest):
    async with get_session() as session:
        result = await session.execute(
            select(Finding).where(Finding.id == uuid.UUID(finding_id))
        )
        finding = result.scalar_one_or_none()
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")

        finding.status = body.status
        finding.actioned_at = (
            datetime.now(timezone.utc) if body.status == "actioned" else None
        )

    return {"id": finding_id, "status": body.status}

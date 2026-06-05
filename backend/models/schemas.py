from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel


class ServiceInfo(BaseModel):
    id: str
    name: str
    description: str
    supported: bool


class IAMPolicyRequest(BaseModel):
    service_ids: list[str]


class IAMPolicyResponse(BaseModel):
    policy: dict[str, Any]
    service_ids: list[str]


class AnalysisRequest(BaseModel):
    service_ids: list[str]
    llm_provider: Literal["anthropic", "gemini", "openai"] = "anthropic"


class CostFinding(BaseModel):
    service: str
    resource_id: str
    resource_type: str
    finding_type: str
    description: str
    estimated_monthly_savings_usd: float
    confidence: Literal["high", "medium", "low"]
    recommendation: str
    metadata: dict[str, Any] = {}


class AnalysisReport(BaseModel):
    run_id: UUID
    timestamp: datetime
    services_analyzed: list[str]
    total_estimated_savings_usd: float
    findings: list[CostFinding]
    llm_provider: str


class FindingActionRequest(BaseModel):
    status: Literal["actioned", "dismissed"]

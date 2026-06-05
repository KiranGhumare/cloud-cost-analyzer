import json

from anthropic import AsyncAnthropic

from ..models.schemas import CostFinding
from .base import LLMProvider

_REPORT_TOOL = {
    "name": "report_cost_findings",
    "description": "Report all identified AWS cost optimisation findings in structured form.",
    "input_schema": {
        "type": "object",
        "properties": {
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "service": {
                            "type": "string",
                            "description": "AWS service identifier, e.g. ebs, ec2, elastic_ip",
                        },
                        "resource_id": {"type": "string"},
                        "resource_type": {"type": "string"},
                        "finding_type": {
                            "type": "string",
                            "description": "Short snake_case label, e.g. unattached_volume, idle_instance",
                        },
                        "description": {
                            "type": "string",
                            "description": "Plain-English explanation of the waste with evidence from telemetry",
                        },
                        "estimated_monthly_savings_usd": {"type": "number"},
                        "confidence": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                        },
                        "recommendation": {
                            "type": "string",
                            "description": "Specific action the customer should take",
                        },
                        "metadata": {
                            "type": "object",
                            "description": "Any additional raw data fields useful for the dashboard",
                        },
                    },
                    "required": [
                        "service",
                        "resource_id",
                        "resource_type",
                        "finding_type",
                        "description",
                        "estimated_monthly_savings_usd",
                        "confidence",
                        "recommendation",
                    ],
                },
            }
        },
        "required": ["findings"],
    },
}

_SYSTEM_PROMPT = """You are an expert AWS cost optimisation analyst.

Analyse the provided AWS resource telemetry and identify every actionable cost-saving opportunity.

Reasoning steps:
1. First identify obviously idle / unused resources (unattached storage, unassociated IPs, stopped-but-billed instances).
2. Then look for overprovisioned resources (large instance types with low utilisation).
3. Flag pricing model mismatches (on-demand instances running 24/7 that qualify for Reserved Instances or Savings Plans).
4. Use conservative, lower-bound savings estimates — never inflate dollar figures.
5. Set confidence: high = unmistakable waste with hard data; medium = strong signal; low = possible waste needing more data.

Always call report_cost_findings — pass an empty list if no waste is found."""


class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def generate_findings(self, telemetry: dict) -> list[CostFinding]:
        user_message = (
            "Here is the AWS resource telemetry. "
            "Analyse it and report all cost optimisation opportunities.\n\n"
            f"```json\n{json.dumps(telemetry, indent=2, default=str)}\n```"
        )

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=_SYSTEM_PROMPT,
            tools=[_REPORT_TOOL],
            tool_choice={"type": "tool", "name": "report_cost_findings"},
            messages=[{"role": "user", "content": user_message}],
        )

        findings: list[CostFinding] = []
        for block in response.content:
            if block.type == "tool_use" and block.name == "report_cost_findings":
                for rf in block.input.get("findings", []):
                    findings.append(
                        CostFinding(
                            service=rf["service"],
                            resource_id=rf["resource_id"],
                            resource_type=rf["resource_type"],
                            finding_type=rf["finding_type"],
                            description=rf["description"],
                            estimated_monthly_savings_usd=rf["estimated_monthly_savings_usd"],
                            confidence=rf["confidence"],
                            recommendation=rf["recommendation"],
                            metadata=rf.get("metadata", {}),
                        )
                    )

        return findings

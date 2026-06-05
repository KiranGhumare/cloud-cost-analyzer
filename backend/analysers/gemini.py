import json

from ..models.schemas import CostFinding
from .base import LLMProvider

_REPORT_SCHEMA = {
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
                        "description": "Additional raw data fields useful for the dashboard",
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


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise ImportError(
                "Install the google-genai package to use this provider: pip install google-genai"
            )

        self.client = genai.Client(api_key=api_key)
        self.model = model
        self._types = types

        self._tool = types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="report_cost_findings",
                    description="Report all identified AWS cost optimisation findings in structured form.",
                    parameters_json_schema=_REPORT_SCHEMA,
                )
            ]
        )

    async def generate_findings(self, telemetry: dict) -> list[CostFinding]:
        types = self._types

        user_message = (
            "Here is the AWS resource telemetry. "
            "Analyse it and report all cost optimisation opportunities.\n\n"
            f"```json\n{json.dumps(telemetry, indent=2, default=str)}\n```"
        )

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                tools=[self._tool],
                tool_config=types.ToolConfig(
                    function_calling_config=types.FunctionCallingConfig(mode="ANY")
                ),
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True
                ),
            ),
        )

        findings: list[CostFinding] = []
        for fc in response.function_calls or []:
            if fc.name == "report_cost_findings":
                for rf in fc.args.get("findings", []):
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

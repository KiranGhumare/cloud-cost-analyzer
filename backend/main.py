from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# from .database import init_db
from .routes.analysis import router as analysis_router
from .routes.services import router as services_router
from backend.agents.graph import app as langgraph_app
from backend.collectors.ec2_collector import collect_underutilised_ec2
from backend.collectors.ebs_collector import collect_ebs_and_elastic_ip_waste
from backend.collectors.cost_explorer_collector import fetch_monthly_spend_by_service


class AnalyseRequest(BaseModel):
    region: str = "us-east-1"
    use_mock_data: bool = False

def get_mock_telemetry() -> dict:
    return {
        "ec2": [
            {
                "instance_id": "i-1234abcd",
                "instance_type": "m5.2xlarge",
                "avg_cpu_percent": 3.2,
                "lookback_days": 14,
                "flag": "underutilised"
            }
        ],
        "storage": [
            {
                "volume_id": "vol-5678efgh",
                "size_gb": 100,
                "volume_type": "gp2",
                "estimated_monthly_cost_usd": 10.0,
                "flag": "unattached_volume"
            },
            {
                "public_ip": "54.123.45.67",
                "allocation_id": "eipalloc-abc123",
                "flag": "unused_elastic_ip"
            }
        ],
        "billing": []
    }

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     await init_db()
#     yield


app = FastAPI(
    title="Cloud Cost Analyser",
    description="Agentic AWS cost analysis powered by GPT-4o and LangGraph",
    version="0.1.0",
    # lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.include_router(services_router)
# app.include_router(analysis_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}

@app.post("/analyse")
async def analyse(request: AnalyseRequest):
    if request.use_mock_data:
        telemetry = get_mock_telemetry()
    else:
        telemetry = {
            "ec2": collect_underutilised_ec2(request.region),
            "storage": collect_ebs_and_elastic_ip_waste(request.region),
            "billing": fetch_monthly_spend_by_service()
        }

    initial_state = {
        "telemetry": telemetry,
        "ec2_findings": [],
        "storage_findings": [],
        "final_findings": [],
        "region": request.region
    }

    result = langgraph_app.invoke(initial_state)

    return {
        "region": request.region,
        "findings": result["final_findings"],
        "telemetry_summary": {
            "ec2_instances_scanned": len(telemetry["ec2"]),
            "storage_resources_scanned": len(telemetry["storage"]),
        }
    }
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routes.analysis import router as analysis_router
from .routes.services import router as services_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Cloud Cost Analyser",
    description="Agentic AWS cost analysis powered by Claude",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(services_router)
app.include_router(analysis_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}

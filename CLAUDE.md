# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All commands run from the project root. The virtualenv is at `.venv/`.

```bash
# Run all tests
.venv/bin/pytest

# Run a single test file
.venv/bin/pytest backend/tests/test_ebs_collector.py -v

# Run a single test by name
.venv/bin/pytest backend/tests/test_ebs_collector.py -v -k "test_estimates_monthly_cost"

# Start the API server
.venv/bin/uvicorn backend.main:app --reload

# Install a new dependency (add to requirements.txt manually after)
.venv/bin/pip install <package>
```

The API auto-documents at `http://localhost:8000/docs` when running.

## Architecture

The pipeline is: **boto3 collectors → LLM provider → FastAPI routes → Postgres**.

### Request flow for `POST /api/analyze`

1. `backend/routes/analysis.py` receives the request with `service_ids` and `llm_provider`
2. It calls each service's collector via `asyncio.to_thread` (collectors are sync boto3, wrapped to avoid blocking the event loop)
3. Raw telemetry dict is passed to the chosen `LLMProvider.generate_findings()`
4. The LLM uses **forced tool use** (`report_cost_findings` tool) to return structured `CostFinding` objects — not free-form text
5. Findings are persisted to Postgres and returned as `AnalysisReport`

### Adding a new collector

1. Write a sync function in `backend/collectors/<service>.py` that takes boto3 client(s) and returns `list[dict]`
2. Register it in `_COLLECTORS` in `backend/routes/analysis.py`
3. Add a `ServiceDefinition` entry in `backend/services/registry.py` with the required IAM actions
4. Write tests using `@mock_aws` from moto (see `backend/tests/test_ebs_collector.py` as the pattern)

### Adding a new LLM provider

1. Subclass `LLMProvider` (`backend/analysers/base.py`) and implement `generate_findings(telemetry: dict) -> list[CostFinding]`
2. Use **forced tool/function calling** to get structured output — the `report_cost_findings` schema is defined in each provider file
3. Use lazy imports inside `__init__` so the provider's package isn't required unless that provider is selected
4. Register in `_PROVIDERS` in `backend/analysers/__init__.py`
5. Add the provider name to the `llm_provider` Literal in `backend/models/schemas.py`
6. Add `<provider>_api_key: str = ""` to `backend/config.py` and the key lookup dict in `backend/routes/analysis.py`

### Key design constraints

- **Collectors are sync** — boto3 has no async API. Always wrap collector calls with `asyncio.to_thread()` in the route, never make them async.
- **Structured output via tool use** — all providers must force a tool call rather than parsing free-form text. Claude uses `tool_choice={"type": "tool", "name": "report_cost_findings"}`; Gemini uses `FunctionCallingConfig(mode="ANY")`.
- **`supported=False` services** — `s3`, `rds`, `lambda` are registered in the service registry (so they appear in the IAM policy generator) but have no collector yet. Don't add them to `_COLLECTORS` until the collector is written.
- **DB is optional for tests** — `backend/database.py` and `backend/config.py` are not imported by collector tests, so tests run without a `.env` file or Postgres.

### Environment

Copy `.env.example` to `.env`. `ANTHROPIC_API_KEY` is required; `GEMINI_API_KEY` and `OPENAI_API_KEY` are optional. `DATABASE_URL` must be a `postgresql+asyncpg://` connection string.

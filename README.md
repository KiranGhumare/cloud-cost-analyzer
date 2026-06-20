# ☁️ Cloud Cost Analyser

> An agentic AI system that autonomously ingests AWS telemetry, performs multi-step cost analysis using a LangGraph multi-agent workflow, and generates prioritised cost reduction recommendations with savings estimates.

![Python](https://img.shields.io/badge/python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green)
![LangGraph](https://img.shields.io/badge/LangGraph-multiagent-orange)
![License](https://img.shields.io/badge/license-MIT-blue)

---

## 🎯 What It Does

Connect your AWS account and the agent will:

- **Scan** your EC2 instances, EBS volumes, Elastic IPs, and billing data
- **Reason** over telemetry using a multi-step LangGraph agent pipeline
- **Identify** waste patterns with chain-of-thought reasoning
- **Recommend** specific, actionable fixes with monthly savings estimates

> Most teams find hundreds to thousands of dollars in savings in their first scan.

---

## 🤖 Agent Architecture

```
POST /analyse
      ↓
Orchestrator Agent         ← analyses telemetry, prepares context
      ↓            ↓
EC2 Analyst     Storage Analyst    ← specialist agents with CoT reasoning
      ↓            ↓
    Synthesis Agent                ← deduplicates, ranks by savings
      ↓
  JSON Findings
```

Each specialist agent uses **chain-of-thought prompting** — reasoning through evidence, pattern, certainty, fix, and confidence before committing to a finding. Low confidence findings are suppressed automatically.

---

## 🔍 What Gets Detected

| Category | What |
|---|---|
| **Compute** | Underutilised EC2 instances (avg CPU < 10% over 14 days) |
| **Storage** | Unattached EBS volumes paying for unused storage |
| **Networking** | Unused Elastic IPs incurring hourly charges |
| **Billing** | Month-over-month spend breakdown by AWS service |

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| **Agent Orchestration** | LangGraph |
| **AI Model** | GPT-4o (OpenAI) |
| **Backend** | Python, FastAPI |
| **AWS Integration** | boto3, CloudWatch API, Cost Explorer API |
| **Testing** | pytest, moto (AWS mocking) |
| **Frontend** | React, Tailwind CSS |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- AWS account with read-only IAM credentials
- OpenAI API key

### 1. Clone the repo
```bash
git clone https://github.com/KiranGhumare/cloud-cost-analyzer.git
cd cloud-cost-analyzer
```

### 2. Set up the backend
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables
```bash
cp .env.example .env
# Fill in your AWS and OpenAI credentials
```

### 4. Run the backend
```bash
uvicorn backend.main:app --reload
```

### 5. Run the frontend
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` and click **Run Analysis**.

---

## 🧪 Try Without AWS Credentials

The API supports a mock data mode — no AWS account needed:

```bash
curl -X POST http://localhost:8000/analyse \
  -H "Content-Type: application/json" \
  -d '{"region": "us-east-1", "use_mock_data": true}'
```

Or just click **Run Analysis** in the dashboard — it uses mock data by default.

---

## 📡 API

### `POST /analyse`

Triggers the full agentic analysis pipeline.

**Request:**
```json
{
  "region": "us-east-1",
  "use_mock_data": false
}
```

**Response:**
```json
{
  "region": "us-east-1",
  "findings": [
    {
      "resource_id": "i-1234abcd",
      "finding_type": "Underutilized Instance",
      "evidence": "m5.2xlarge running at 3.2% avg CPU over 14 days",
      "recommendation": "Downsize to m5.large",
      "estimated_monthly_saving": 207.36,
      "confidence": "High"
    }
  ],
  "telemetry_summary": {
    "ec2_instances_scanned": 3,
    "storage_resources_scanned": 5
  }
}
```

### `GET /health`

```json
{"status": "ok", "version": "0.1.0"}
```

---

## 🧪 Running Tests

```bash
python -m pytest backend/tests/ -v
```

All collectors are tested with moto — no real AWS account needed to run tests.

---

## 📁 Project Structure

```
cloud-cost-analyzer/
├── backend/
│   ├── agents/
│   │   ├── state.py              # LangGraph state definition
│   │   ├── analyst_agents.py     # Orchestrator, EC2, Storage, Synthesis agents
│   │   └── graph.py              # LangGraph workflow
│   ├── collectors/
│   │   ├── ec2_collector.py      # EC2 CPU utilisation collector
│   │   ├── ebs_collector.py      # EBS + Elastic IP collector
│   │   └── cost_explorer_collector.py  # AWS billing data collector
│   ├── tests/
│   │   ├── test_ec2_collector.py
│   │   ├── test_ebs_collector.py
│   │   └── test_cost_explorer_collector.py
│   ├── main.py                   # FastAPI app + /analyse endpoint
│   └── config.py                 # Settings from .env
├── frontend/
│   └── src/
│       └── App.jsx               # React dashboard
├── .env.example
└── README.md
```

---

## 🗺️ Roadmap

- [x] EC2 underutilisation detection
- [x] EBS unattached volume detection
- [x] Unused Elastic IP detection
- [x] Cost Explorer billing analysis
- [x] LangGraph multi-agent orchestration
- [x] Chain-of-thought prompting
- [x] React dashboard
- [ ] Lambda over-provisioned memory detection
- [ ] Idle NAT Gateway detection
- [ ] Evaluation framework (F1, hallucination rate)
- [ ] Langfuse observability
- [ ] RAG pipeline for real-time AWS pricing
- [ ] Celery + Redis scheduled scans
- [ ] PostgreSQL scan history

---

## 👤 Author

**Kiran Ghumare**
[github.com/KiranGhumare](https://github.com/KiranGhumare)

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
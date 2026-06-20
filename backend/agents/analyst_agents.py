from openai import OpenAI
import json
import re
from backend.agents.state import AnalysisState
from backend.config import settings

client = OpenAI(api_key=settings.openai_api_key)

def orchestrator_node(state: AnalysisState) -> AnalysisState:
    telemetry = state["telemetry"]
    
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1000,
        messages = [
            {"role": "system", "content": """You are a cloud cost orchestration agent. 
You receive AWS telemetry and prepare focused data slices for specialist agents.
Think step by step:
1. What resources are present in this telemetry?
2. What waste patterns might exist?
3. Summarise the key data points each specialist needs.

Respond with a brief analysis of what you found and what the specialists should focus on."""
            },
            {"role": "user", "content": f"Analyse this AWS telemetry and identify areas of potential waste:\n{telemetry}"}
        ]
    )
    
    print(f"Orchestrator: {response.choices[0].message.content[:200]}...")
    return state


def ec2_analyst_node(state: AnalysisState) -> AnalysisState:
    ec2_data = state["telemetry"].get("ec2", [])
    
    if not ec2_data:
        state["ec2_findings"] = []
        return state
    
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=2000,
        messages = [
            {"role": "system", "content": """You are an EC2 cost optimisation specialist.

Before producing ANY finding, think through these steps:
<thinking>
1. EVIDENCE: What exactly does the data show? (CPU%, days running, instance type)
2. PATTERN: What waste pattern does this match? (idle, over-provisioned)
3. CERTAINTY: Am I sure this is waste or could there be a legitimate reason?
4. FIX: What is the single most specific action to take?
5. SAVING: What is the realistic monthly saving in dollars?
6. CONFIDENCE: High / Medium / Low — and why?
</thinking>

Only output a finding if confidence is Medium or High.
Never invent resource IDs. Only reference resources in the data provided.
Return findings as a JSON array. If no findings, return [].
Each finding must have: resource_id, finding_type, evidence, recommendation, estimated_monthly_saving, confidence"""},
            {"role": "user", "content": f"Analyse this EC2 telemetry for waste:\n{ec2_data}"}
        ]
    )
    
    text = response.choices[0].message.content
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    json_match = re.search(r'\[.*\]', text, re.DOTALL)
    if json_match:
        try:
            state["ec2_findings"] = json.loads(json_match.group())
        except json.JSONDecodeError:
            state["ec2_findings"] = []
    else:
        state["ec2_findings"] = []

    return state

def storage_analyst_node(state: AnalysisState) -> AnalysisState:
    storage_data = state["telemetry"].get("storage", [])

    if not storage_data:
        state["storage_findings"] = []
        return state
    
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=2000,
        messages = [
            {"role": "system", "content": """You are a Storage cost optimisation specialist.
        
Before producing ANY finding, think through these steps:
<thinking>
1. EVIDENCE: What exactly does the data show? (storage used, number of volumes reserved, elastic ips)
2. PATTERN: What waste pattern does this match? (unused volumes with very less size)
3. CERTAINTY: Am I sure this is waste or could there be a legitimate reason?
4. FIX: What is the single most specific action to take?
5. SAVING: What is the realistic monthly saving in dollars?
6. CONFIDENCE: High / Medium / Low — and why?
</thinking>

Only output a finding if confidence is Medium or High.
Never invent resource IDs. Only reference resources in the data provided.
Return findings as a JSON array. If no findings, return [].
Each finding must have: resource_id, finding_type, evidence, recommendation, estimated_monthly_saving, confidence"""},
            {"role": "user", "content": f"Analyse this storage telemetry for waste:\n{storage_data}"}
        ]
    )
    text = response.choices[0].message.content
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    json_match = re.search(r'\[.*\]', text, re.DOTALL)
    if json_match:
        try:
            state["storage_findings"] = json.loads(json_match.group())
        except json.JSONDecodeError:
            state["storage_findings"] = []
    else:
        state["storage_findings"] = []
    
    return state

    
def synthesis_node(state: AnalysisState):
    ec2_findings = state["ec2_findings"]
    storage_findings = state["storage_findings"]
    final_findings = ec2_findings + storage_findings

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=2000,
        messages =[
            {"role": "system", "content":"""You are a cloud cost synthesis agent.
You have received findings from multiple specialist agents.

Think step by step:
1. Are there duplicate findings about the same resource? Merge them.
2. Rank all findings by estimated_monthly_saving, highest first.
3. What is the total potential monthly saving?

Return a JSON array of deduplicated, ranked findings.
Add a field "total_potential_saving" as the last item.
"""},
            {"role": "user", "content": f"Analyse cloud cost and saving potential for:\n{final_findings}"}
        ]
    )
    text = response.choices[0].message.content
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    json_match = re.search(r'\[.*\]', text, re.DOTALL)
    if json_match:
        try:
            state["final_findings"] = json.loads(json_match.group())
        except json.JSONDecodeError:
            state["final_findings"] = []
    else:
        state["final_findings"] = []

    return state

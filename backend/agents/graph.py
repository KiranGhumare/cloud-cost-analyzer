from langgraph.graph import StateGraph, END
from backend.agents.state import AnalysisState
from backend.agents.analyst_agents import (
    orchestrator_node,
    ec2_analyst_node,
    storage_analyst_node,
    synthesis_node,
)

def build_graph():
    graph = StateGraph(AnalysisState)
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("ec2_analyst", ec2_analyst_node)
    graph.add_node("storage_analyst", storage_analyst_node)
    graph.add_node("synthesis", synthesis_node)

    graph.set_entry_point("orchestrator")
    graph.add_edge("orchestrator", "ec2_analyst")
    graph.add_edge("orchestrator", "storage_analyst")
    graph.add_edge("ec2_analyst", "synthesis")
    graph.add_edge("storage_analyst", "synthesis")
    graph.add_edge("synthesis", END)
    
    return graph.compile()

app = build_graph()
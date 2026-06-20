from typing import TypedDict, Annotated
import operator

class AnalysisState(TypedDict):
    telemetry: Annotated[dict, lambda x, y: {**x, **y}]
    ec2_findings: Annotated[list, operator.add]    
    storage_findings: Annotated[list, operator.add]  
    final_findings: Annotated[list, operator.add]   
    region: Annotated[str, lambda x, y: x]
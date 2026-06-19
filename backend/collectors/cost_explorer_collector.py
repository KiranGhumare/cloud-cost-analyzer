import boto3
import datetime
from typing import Any

LOOKBACK_MONTHS = 1

def get_ce_client() -> Any:
    return boto3.client("ce", region_name="us-east-1")


def fetch_monthly_spend_by_service() -> list[dict]:
    result = []
    ce = get_ce_client()
    today = datetime.date.today()
    first_day_this_month = today.replace(day=1)
    last_day_last_month = first_day_this_month - datetime.timedelta(days=1)
    first_day_last_month = last_day_last_month.replace(day=1)

    response = ce.get_cost_and_usage(
        TimePeriod = {"Start": first_day_last_month.isoformat() , "End": first_day_this_month.isoformat()},
        Granularity = "MONTHLY",
        GroupBy = [{"Type": "DIMENSION", "Key": "SERVICE"}],
        Metrics = ["BlendedCost"]
    )

    if not response["ResultsByTime"]:
        return []
    
    for item in response["ResultsByTime"][0]["Groups"]:
        if float(item["Metrics"]["BlendedCost"]["Amount"]) > 0:
            result.append({
                "service": item["Keys"][0],
                "amount_usd": round(float(item["Metrics"]["BlendedCost"]["Amount"]), 2),
            })

    return result


COST_EXPLORER_COLLECTOR_TOOL_DEFINITION = {
    "name": "get_monthly_spend_by_service",
    "description":(
        "Fetch last month's AWS spend broken down by service (EC2, S3, RDS etc). "
        "Returns service name and amount in USD. Use this to identify which services are the biggest cost drivers before diving into specific resource analysis. "
    ),
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}
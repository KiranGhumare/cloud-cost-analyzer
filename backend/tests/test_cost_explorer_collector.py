import boto3
import pytest
from moto import mock_aws
from backend.collectors.cost_explorer_collector import (
    fetch_monthly_spend_by_service,
)

REGION = "us-east-1"

@mock_aws
def test_fetch_monthly_spend_returns_empty_when_no_spend():
    result = fetch_monthly_spend_by_service()
    assert isinstance(result, list)

@mock_aws
def test_fetch_monthly_spend_returns_list_of_dicts():
    result = fetch_monthly_spend_by_service()
    assert isinstance(result, list)
    for item in result:
        assert "service" in item
        assert "amount_usd" in item
        assert isinstance(item["amount_usd"], float)

@mock_aws
def test_fetch_monthly_spend_excludes_zero_spend_services():
    result = fetch_monthly_spend_by_service()
    for item in result:
        assert item["amount_usd"] > 0
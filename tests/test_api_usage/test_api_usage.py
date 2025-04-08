"""
Test for API usage statistics functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.api_usage import get_api_usage, display_usage_stats
import json
import os
from io import StringIO
from datetime import datetime, timedelta

@pytest.fixture
def mock_api_usage_data():
    """Fixture with mock API usage data"""
    today = datetime.now().strftime("%Y-%m-%d")
    current_month = datetime.now().strftime("%Y-%m")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    last_month = (datetime.now() - timedelta(days=30)).strftime("%Y-%m")
    
    return {
        "total_calls": 1250,
        "calls_today": 45,
        "first_call_date": yesterday,
        "last_call_date": today,
        "rate_limit_info": {
            "api_key": "demo_key",
            "limit": 10000,
            "remaining": 8750,
            "reset": int((datetime.now() + timedelta(hours=1)).timestamp()),
            "credits_monthly_limit": 10000,
            "credits_used_month": 1250,
            "credits_remaining_month": 8750,
            "credits_remaining_minute": 50,
            "credits_remaining_second": 10
        },
        "daily_calls": {
            yesterday: 75,
            today: 45
        },
        "monthly_usage": {
            last_month: 980,
            current_month: 1250
        },
        "endpoints_called": {
            "simple/price": 450,
            "coins/markets": 275,
            "search/trending": 120,
            "global": 85,
            "global/decentralized_finance_defi": 65,
            "search": 50,
            "coins/bitcoin/market_chart": 45,
            "coins/bitcoin/ohlc": 40,
            "coins/ethereum/market_chart": 35,
            "asset_platforms": 30,
            "simple/supported_vs_currencies": 25,
            "companies/public_treasury/bitcoin": 15,
            "companies/public_treasury/ethereum": 15
        }
    }

@pytest.fixture
def mock_empty_usage_data():
    """Fixture with empty API usage data"""
    return {
        "total_calls": 0,
        "calls_today": 0,
        "first_call_date": None,
        "last_call_date": None,
        "rate_limit_info": {},
        "monthly_usage": {},
        "endpoints_called": {}
    }

def test_get_api_usage_without_refresh(monkeypatch):
    """Test getting API usage stats without forcing a refresh"""
    # Create a mock API instance
    mock_api = MagicMock()
    mock_api.get_usage_stats.return_value = {"total_calls": 100}
    
    # Patch the API instance
    monkeypatch.setattr("app.api_usage.api", mock_api)
    
    # Call the function without forcing refresh
    result = get_api_usage(force_refresh=False)
    
    # Assert that we didn't make an API call
    assert not mock_api.get_supported_vs_currencies.called
    
    # Assert that we got the expected result
    assert result == {"total_calls": 100}
    assert mock_api.get_usage_stats.call_count == 1

def test_get_api_usage_with_refresh(monkeypatch):
    """Test getting API usage stats with forcing a refresh"""
    # Create a mock API instance
    mock_api = MagicMock()
    mock_api.get_usage_stats.return_value = {"total_calls": 100}
    
    # Patch the API instance
    monkeypatch.setattr("app.api_usage.api", mock_api)
    
    # Call the function with forcing refresh
    result = get_api_usage(force_refresh=True)
    
    # Assert that we made an API call
    assert mock_api.get_supported_vs_currencies.called
    
    # Assert that we got the expected result
    assert result == {"total_calls": 100}
    assert mock_api.get_usage_stats.call_count == 1

def test_display_usage_stats(mock_api_usage_data, monkeypatch, capsys):
    """Test displaying API usage statistics"""
    # Create a StringIO object to capture rich console output
    console_output = StringIO()
    
    # Create a mock console
    mock_console = MagicMock()
    mock_console.print = lambda *args, **kwargs: console_output.write(str(args[0]) + '\n')
    
    # Patch the console
    monkeypatch.setattr("app.api_usage.console", mock_console)
    
    # Call the function
    display_usage_stats(mock_api_usage_data)
    
    # Get the output
    output = console_output.getvalue()
    
    # Check that the main sections are in the output
    assert "CoinGecko API Usage Statistics" in output
    assert "Basic Usage Information" in output
    assert "Rate Limit Information" in output
    assert "Monthly Usage" in output
    assert "Endpoint Usage" in output
    assert "Recommendations" in output
    
    # Check that key information is displayed
    assert "Total calls: 1.25K" in output
    assert "Calls today: 45" in output
    assert "API Key: demo_key" in output
    assert "Monthly credit limit: 10K" in output
    assert "Credits remaining this month: 8.75K" in output

def test_display_usage_stats_empty(mock_empty_usage_data, monkeypatch, capsys):
    """Test displaying empty API usage statistics"""
    # Create a StringIO object to capture rich console output
    console_output = StringIO()
    
    # Create a mock console
    mock_console = MagicMock()
    mock_console.print = lambda *args, **kwargs: console_output.write(str(args[0]) + '\n')
    
    # Patch the console
    monkeypatch.setattr("app.api_usage.console", mock_console)
    
    # Call the function
    display_usage_stats(mock_empty_usage_data)
    
    # Get the output
    output = console_output.getvalue()
    
    # Check that the main sections are in the output
    assert "CoinGecko API Usage Statistics" in output
    assert "Basic Usage Information" in output
    
    # Check that key information is displayed
    assert "Total calls: 0" in output
    assert "Calls today: 0" in output
    assert "First API call: Never" in output
    assert "Last API call: Never" in output
    
    # Rate limit info section shouldn't have detailed content
    assert "Monthly credit limit" not in output
    assert "Credits used this month" not in output

def test_save_api_usage_export(mock_api_usage_data, tmp_path):
    """Test saving API usage data to a file"""
    from app.api_usage import save_api_usage_export
    
    # Use a temporary file path
    output_file = tmp_path / "test_usage_export.json"
    
    # Save the data
    result_path = save_api_usage_export(mock_api_usage_data, str(output_file))
    
    # Assert the file exists
    assert os.path.exists(result_path)
    
    # Read the file and verify content
    with open(result_path, 'r') as f:
        saved_data = json.load(f)
    
    # Verify the saved data matches the input
    assert saved_data == mock_api_usage_data
    assert saved_data["total_calls"] == 1250
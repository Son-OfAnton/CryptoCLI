"""
Pytest configuration and shared fixtures.
"""
import pytest
from unittest.mock import patch, MagicMock
import os
import json
from io import StringIO
import sys

# Sample API responses for testing
@pytest.fixture
def mock_simple_price_response():
    """Mock response for the CoinGecko simple/price endpoint"""
    return {
        "bitcoin": {
            "usd": 57234.78
        }
    }

@pytest.fixture
def mock_detailed_price_response():
    """Mock response for the CoinGecko markets endpoint"""
    return [
        {
            "id": "bitcoin",
            "symbol": "btc",
            "name": "Bitcoin",
            "image": "https://assets.coingecko.com/coins/images/1/large/bitcoin.png",
            "current_price": 57234.78,
            "market_cap": 1120300000000,
            "market_cap_rank": 1,
            "fully_diluted_valuation": 1200000000000,
            "total_volume": 65432000000,
            "high_24h": 58345.67,
            "low_24h": 56123.45,
            "price_change_24h": -567.89,
            "price_change_percentage_24h": -0.98,
            "market_cap_change_24h": -12345678.0,
            "market_cap_change_percentage_24h": -1.1,
            "circulating_supply": 19565000.0,
            "total_supply": 21000000.0,
            "max_supply": 21000000.0,
            "last_updated": "2025-03-31T12:34:56.789Z"
        }
    ]

@pytest.fixture
def mock_empty_response():
    """Mock empty response"""
    return {}

@pytest.fixture
def mock_error_response():
    """Mock error response from API"""
    class MockErrorResponse:
        def __init__(self):
            self.status_code = 429
            self.reason = "Too Many Requests"
            
        def raise_for_status(self):
            raise Exception(f"HTTP Error: {self.status_code} - {self.reason}")
            
    return MockErrorResponse()

@pytest.fixture
def mock_api():
    """Create a mock CoinGeckoAPI instance"""
    with patch('CryptoCLI.api.CoinGeckoAPI') as MockAPI:
        mock_instance = MagicMock()
        MockAPI.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def capture_stdout():
    """Capture stdout for testing console output"""
    captured_output = StringIO()
    sys.stdout = captured_output
    yield captured_output
    sys.stdout = sys.__stdout__

@pytest.fixture(autouse=True)
def setup_environment():
    """Setup environment variables for testing"""
    # Save original environment
    original_env = os.environ.copy()
    
    # Set test environment variables
    os.environ["COINGECKO_BASE_URL"] = "https://api.coingecko.com/api/v3"
    os.environ["COINGECKO_API_KEY"] = "test_api_key"
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
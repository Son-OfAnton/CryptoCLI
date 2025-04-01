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

@pytest.fixture
def mock_multiple_crypto_price_response():
    """Mock response for multiple cryptocurrencies in the simple/price endpoint"""
    return {
        "bitcoin": {
            "usd": 57234.78
        },
        "ethereum": {
            "usd": 2845.62
        },
        "litecoin": {
            "usd": 156.92
        },
        "ripple": {
            "usd": 0.58
        },
        "cardano": {
            "usd": 0.45
        }
    }

@pytest.fixture
def mock_multiple_markets_response():
    """Mock response for multiple cryptocurrencies in the markets endpoint"""
    return [
        {
            "id": "bitcoin",
            "symbol": "btc",
            "name": "Bitcoin",
            "current_price": 57234.78,
            "market_cap": 1120300000000,
            "market_cap_rank": 1,
            "price_change_percentage_24h": -0.98,
            "total_volume": 65432000000
        },
        {
            "id": "ethereum",
            "symbol": "eth",
            "name": "Ethereum",
            "current_price": 2845.62,
            "market_cap": 345600000000,
            "market_cap_rank": 2,
            "price_change_percentage_24h": 1.25,
            "total_volume": 23456000000
        },
        {
            "id": "binancecoin",
            "symbol": "bnb",
            "name": "BNB",
            "current_price": 598.34,
            "market_cap": 92300000000,
            "market_cap_rank": 3,
            "price_change_percentage_24h": -2.15,
            "total_volume": 1234567890
        },
        {
            "id": "cardano",
            "symbol": "ada",
            "name": "Cardano",
            "current_price": 0.45,
            "market_cap": 15800000000,
            "market_cap_rank": 8,
            "price_change_percentage_24h": 1.05,
            "total_volume": 589000000
        },
        {
            "id": "solana",
            "symbol": "sol",
            "name": "Solana",
            "current_price": 138.25,
            "market_cap": 62400000000,
            "market_cap_rank": 5,
            "price_change_percentage_24h": 2.35,
            "total_volume": 1765000000
        }
    ]
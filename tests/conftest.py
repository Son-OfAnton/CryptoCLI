"""
Test fixtures and utility functions for testing the CryptoCLI application.
"""
import pytest
from unittest.mock import MagicMock, patch
import os
import io
import sys

# ========== PRICE API FIXTURES ==========

@pytest.fixture
def mock_simple_price_response():
    """Mock response for the simple/price endpoint"""
    return {
        "bitcoin": {
            "usd": 40000.0,
            "eur": 34000.0,
        }
    }

@pytest.fixture
def mock_detailed_price_response():
    """Mock response for the markets endpoint with more detailed price/market data"""
    return [
        {
            "id": "bitcoin",
            "symbol": "btc",
            "name": "Bitcoin",
            "current_price": 40000.0,
            "market_cap": 750000000000,
            "market_cap_rank": 1,
            "total_volume": 25000000000,
            "high_24h": 41000.0,
            "low_24h": 39000.0,
            "price_change_24h": 1000.0,
            "price_change_percentage_24h": 2.5,
            "market_cap_change_24h": 12500000000,
            "market_cap_change_percentage_24h": 1.5,
            "circulating_supply": 18750000,
            "total_supply": 21000000,
            "max_supply": 21000000,
            "last_updated": "2023-07-01T00:00:00.000Z"
        }
    ]

@pytest.fixture
def mock_empty_response():
    """Empty response for testing edge cases"""
    return {}

@pytest.fixture
def mock_error_response():
    """Mock for API error responses"""
    class MockErrorResponse:
        def __init__(self):
            self.status_code = 429
            self.reason = "Too Many Requests"
        
        def raise_for_status(self):
            raise Exception(f"{self.status_code}: {self.reason}")
    
    return MockErrorResponse()

@pytest.fixture
def mock_api():
    """Mock the entire CoinGeckoAPI class"""
    mock = MagicMock()
    mock.get_price.return_value = {}  # Default empty response
    return mock

@pytest.fixture
def capture_stdout():
    """Capture stdout for testing console output"""
    captured_output = io.StringIO()
    sys.stdout = captured_output
    yield captured_output
    sys.stdout = sys.__stdout__

@pytest.fixture
def setup_environment():
    """Set up environment variables required for testing"""
    # Store original environment variables
    old_env = dict(os.environ)
    
    # Set required environment variables for testing
    os.environ["COINGECKO_BASE_URL"] = "https://api.coingecko.com/api/v3"
    os.environ["COINGECKO_API_KEY"] = "test_api_key"
    
    # Return control to the test
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(old_env)

@pytest.fixture
def mock_multiple_crypto_price_response():
    """Mock response for multiple cryptocurrencies from the simple/price endpoint"""
    return {
        "bitcoin": {
            "usd": 40000.0,
            "eur": 33000.0,
            "btc": 1.0
        },
        "ethereum": {
            "usd": 2000.0,
            "eur": 1650.0,
            "btc": 0.05
        },
        "litecoin": {
            "usd": 100.0,
            "eur": 82.5,
            "btc": 0.0025
        }
    }

@pytest.fixture
def mock_multiple_markets_response():
    """Mock response for multiple cryptocurrencies from the markets endpoint"""
    return [
        {
            "id": "bitcoin",
            "symbol": "btc",
            "name": "Bitcoin",
            "current_price": 40000.0,
            "market_cap": 750000000000,
            "price_change_percentage_24h": 2.5,
            "total_volume": 25000000000
        },
        {
            "id": "ethereum",
            "symbol": "eth",
            "name": "Ethereum",
            "current_price": 2000.0,
            "market_cap": 240000000000,
            "price_change_percentage_24h": -1.2,
            "total_volume": 15000000000
        },
        {
            "id": "litecoin",
            "symbol": "ltc",
            "name": "Litecoin",
            "current_price": 100.0,
            "market_cap": 7000000000,
            "price_change_percentage_24h": 0.8,
            "total_volume": 500000000
        }
    ]

@pytest.fixture
def mock_trending_coins_response():
    """Mock response for the search/trending endpoint with coins data"""
    return {
        "coins": [
            {
                "item": {
                    "id": "bitcoin",
                    "name": "Bitcoin",
                    "symbol": "BTC",
                    "market_cap_rank": 1,
                    "price_btc": 1.0,
                    "score": 0
                }
            },
            {
                "item": {
                    "id": "ethereum",
                    "name": "Ethereum",
                    "symbol": "ETH",
                    "market_cap_rank": 2,
                    "price_btc": 0.05,
                    "score": 1
                }
            },
            {
                "item": {
                    "id": "solana",
                    "name": "Solana",
                    "symbol": "SOL",
                    "market_cap_rank": 5,
                    "price_btc": 0.0025,
                    "score": 2
                }
            }
        ],
        "nfts": [],  # Empty NFTs for coin-only test
        "updated_at": 1627851600  # Timestamp example: August 1, 2021
    }

@pytest.fixture
def mock_trending_nfts_response():
    """Mock response for the search/trending endpoint with NFTs data"""
    return {
        "coins": [],  # Empty coins for NFT-only test
        "nfts": [
            {
                "item": {
                    "id": "bored-ape-yacht-club",
                    "name": "Bored Ape Yacht Club",
                    "symbol": "BAYC",
                    "thumb": "https://example.com/bayc.png",
                    "floor_price_in_eth": 45.5,
                    "market_cap": 450000000,
                    "volume_24h": 5600000,
                    "floor_price_24h_percentage_change": 2.5,
                    "score": 0
                }
            },
            {
                "item": {
                    "id": "cryptopunks",
                    "name": "CryptoPunks",
                    "symbol": "PUNK",
                    "thumb": "https://example.com/cryptopunks.png",
                    "floor_price_in_eth": 60.2,
                    "market_cap": 600000000,
                    "volume_24h": 7800000,
                    "floor_price_24h_percentage_change": -1.2,
                    "score": 1
                }
            },
            {
                "item": {
                    "id": "azuki",
                    "name": "Azuki",
                    "symbol": "AZUKI",
                    "thumb": "https://example.com/azuki.png",
                    "floor_price_in_eth": 15.3,
                    "market_cap": 150000000,
                    "volume_24h": 2100000,
                    "floor_price_24h_percentage_change": 5.3,
                    "score": 2
                }
            }
        ],
        "updated_at": 1627851600  # Timestamp example: August 1, 2021
    }

@pytest.fixture
def mock_trending_combined_response():
    """Mock response for the search/trending endpoint with both coins and NFTs data"""
    return {
        "coins": [
            {
                "item": {
                    "id": "bitcoin",
                    "name": "Bitcoin",
                    "symbol": "BTC",
                    "market_cap_rank": 1,
                    "price_btc": 1.0,
                    "score": 0
                }
            },
            {
                "item": {
                    "id": "ethereum",
                    "name": "Ethereum",
                    "symbol": "ETH",
                    "market_cap_rank": 2,
                    "price_btc": 0.05,
                    "score": 1
                }
            }
        ],
        "nfts": [
            {
                "item": {
                    "id": "bored-ape-yacht-club",
                    "name": "Bored Ape Yacht Club",
                    "symbol": "BAYC",
                    "floor_price_in_eth": 45.5,
                    "market_cap": 450000000,
                    "volume_24h": 5600000,
                    "score": 0
                }
            },
            {
                "item": {
                    "id": "cryptopunks",
                    "name": "CryptoPunks",
                    "symbol": "PUNK",
                    "floor_price_in_eth": 60.2,
                    "market_cap": 600000000,
                    "volume_24h": 7800000,
                    "score": 1
                }
            }
        ],
        "updated_at": 1627851600  # Timestamp example: August 1, 2021
    }
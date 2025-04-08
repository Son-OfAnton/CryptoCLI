"""
API module for interacting with the CoinGecko API directly using requests.
"""
import requests
import time
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional

load_dotenv()


class CoinGeckoAPI:
    """Class for direct interaction with the CoinGecko API."""

    COINGECKO_BASE_URL = os.getenv("COINGECKO_BASE_URL")
    if COINGECKO_BASE_URL is None:
        raise ValueError(
            "COINGECKO_BASE_URL not set in environment variables.")
    COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
    if COINGECKO_API_KEY is None:
        raise ValueError("COINGECKO_API_KEY not set in environment variables.")

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "CryptoStats CLI/0.1.0",
            'x-cg-api-key': self.COINGECKO_API_KEY
        })
        self.last_request_time = 0
        # Wait at least 1.5s between requests to respect rate limits
        self.rate_limit_wait = 1.5
        
        # Usage tracking properties
        self.usage_data = {
            "total_calls": 0,
            "calls_today": 0,
            "first_call_date": None,
            "last_call_date": None,
            "rate_limit_info": {},
            "monthly_usage": {},
            "endpoints_called": {}
        }
        self._load_usage_data()

    def _respect_rate_limit(self):
        """Ensures we don't exceed rate limits by enforcing delays between requests."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time

        if elapsed < self.rate_limit_wait:
            time.sleep(self.rate_limit_wait - elapsed)

        self.last_request_time = time.time()

    def _extract_rate_limit_headers(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Extract rate limit information from response headers."""
        rate_limit_info = {}
        
        # Common rate limit headers from APIs
        headers_to_extract = {
            "x-ratelimit-limit": "limit",
            "x-ratelimit-remaining": "remaining",
            "x-ratelimit-reset": "reset",
            "x-cg-pro-api-key": "api_key",
            "x-cg-api-credits-remaining-second": "credits_remaining_second",
            "x-cg-api-credits-remaining-minute": "credits_remaining_minute",
            "x-cg-api-credits-remaining-month": "credits_remaining_month",
            "x-cg-api-credits-used-month": "credits_used_month",
            "x-cg-api-credit-monthly-limit": "credits_monthly_limit"
        }
        
        # Extract headers if they exist
        for header, key in headers_to_extract.items():
            if header in headers:
                try:
                    # Try to convert to int for numeric values
                    rate_limit_info[key] = int(headers[header])
                except (ValueError, TypeError):
                    # If conversion fails, store as string
                    rate_limit_info[key] = headers[header]
        
        return rate_limit_info

    def _update_usage_stats(self, endpoint: str, rate_limit_info: Dict[str, Any]):
        """Update API usage statistics."""
        today = datetime.now().strftime("%Y-%m-%d")
        current_month = datetime.now().strftime("%Y-%m")
        
        # Update total call count
        self.usage_data["total_calls"] += 1
        
        # Set first call date if not set
        if not self.usage_data["first_call_date"]:
            self.usage_data["first_call_date"] = today
            
        # Update last call date
        self.usage_data["last_call_date"] = today
        
        # Update calls today
        if "daily_calls" not in self.usage_data:
            self.usage_data["daily_calls"] = {}
        
        if today not in self.usage_data["daily_calls"]:
            self.usage_data["daily_calls"][today] = 0
            
        self.usage_data["daily_calls"][today] += 1
        self.usage_data["calls_today"] = self.usage_data["daily_calls"][today]
        
        # Update monthly usage
        if current_month not in self.usage_data["monthly_usage"]:
            self.usage_data["monthly_usage"][current_month] = 0
            
        self.usage_data["monthly_usage"][current_month] += 1
        
        # Update endpoints called
        if endpoint not in self.usage_data["endpoints_called"]:
            self.usage_data["endpoints_called"][endpoint] = 0
            
        self.usage_data["endpoints_called"][endpoint] += 1
        
        # Update rate limit information
        if rate_limit_info:
            self.usage_data["rate_limit_info"] = rate_limit_info
        
        # Save updated usage data
        self._save_usage_data()

    def _load_usage_data(self):
        """Load API usage statistics from file if it exists."""
        usage_file = os.path.expanduser("~/.coingecko_usage.json")
        
        try:
            if os.path.exists(usage_file):
                with open(usage_file, 'r') as f:
                    saved_data = json.load(f)
                    self.usage_data.update(saved_data)
        except Exception as e:
            # If there's an error loading the file, continue with default values
            pass

    def _save_usage_data(self):
        """Save API usage statistics to file."""
        usage_file = os.path.expanduser("~/.coingecko_usage.json")
        
        try:
            with open(usage_file, 'w') as f:
                json.dump(self.usage_data, f, indent=4)
        except Exception as e:
            # If there's an error saving the file, just continue
            pass

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get current API usage statistics.
        
        Returns:
            Dict containing usage statistics
        """
        return self.usage_data

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Make a request to the CoinGecko API.

        Args:
            endpoint: API endpoint to call
            params: Query parameters for the request

        Returns:
            JSON response as a dictionary
        """
        self._respect_rate_limit()
        url = f"{self.COINGECKO_BASE_URL}/{endpoint}"

        try:
            response = self.session.get(url, params=params, timeout=10)
            
            # Extract and store rate limit information
            rate_limit_info = self._extract_rate_limit_headers(response.headers)
            self._update_usage_stats(endpoint, rate_limit_info)
            
            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"API request error: {str(e)}"
            # You might want to log this error in a production environment
            raise Exception(error_msg)

    def get_price(self, coin_ids: List[str], vs_currencies: List[str]) -> Dict[str, Dict[str, float]]:
        """
        Get current prices for a list of coins in specific currencies.

        Args:
            coin_ids: List of coin IDs (e.g., 'bitcoin', 'ethereum')
            vs_currencies: List of currencies to get prices in (e.g., 'usd', 'eur')

        Returns:
            Dictionary with coin IDs as keys and price data as values
        """
        params = {
            "ids": ",".join(coin_ids),
            "vs_currencies": ",".join(vs_currencies)
        }
        return self._make_request("simple/price", params)

    def get_coin_markets(self, vs_currency: str = 'usd', count: int = 10,
                         page: int = 1, order: str = 'market_cap_desc') -> List[Dict[str, Any]]:
        """
        Get list of coins with market data ordered by criteria.

        Args:
            vs_currency: Currency to get market data in
            count: Number of results per page
            page: Page number
            order: Sorting method (market_cap_desc, gecko_desc, gecko_asc, market_cap_asc, etc.)

        Returns:
            List of coins with market data
        """
        params = {
            "vs_currency": vs_currency,
            "per_page": count,
            "page": page,
            "order": order,
            "sparkline": False
        }
        return self._make_request("coins/markets", params)

    def get_coin_data(self, coin_id: str) -> Dict[str, Any]:
        """
        Get detailed data for a specific coin.

        Args:
            coin_id: ID of the coin

        Returns:
            Detailed coin data
        """
        params = {
            "localization": "false",
            "tickers": "true",
            "market_data": "true",
            "community_data": "true",
            "developer_data": "true"
        }
        return self._make_request(f"coins/{coin_id}", params)

    def get_coin_market_chart(self, coin_id: str, vs_currency: str = 'usd',
                              days: int = 7, interval: str = 'daily') -> Dict[str, List]:
        """
        Get historical market data for a coin over time.

        Args:
            coin_id: ID of the coin
            vs_currency: Currency to get market data in
            days: Number of days of data to return
            interval: Data interval (daily, hourly)

        Returns:
            Historical market data
        """
        params = {
            "vs_currency": vs_currency,
            "days": days,
            "interval": interval
        }
        return self._make_request(f"coins/{coin_id}/market_chart", params)

    def get_coin_market_chart_range(self, coin_id: str, vs_currency: str,
                                    from_timestamp: int, to_timestamp: int) -> Dict[str, List]:
        """
        Get historical market data for a coin within a specific date range.

        Args:
            coin_id: ID of the coin
            vs_currency: Currency to get market data in
            from_timestamp: From date in UNIX timestamp
            to_timestamp: To date in UNIX timestamp

        Returns:
            Historical market data within date range
        """
        params = {
            "vs_currency": vs_currency,
            "from": from_timestamp,
            "to": to_timestamp
        }
        return self._make_request(f"coins/{coin_id}/market_chart/range", params)

    def get_trending_coins(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get trending coins in the last 24 hours.

        Returns:
            Trending coins data
        """
        return self._make_request("search/trending")
    
    def get_trending_nfts(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get trending NFTs in the last 24 hours.

        Returns:
            Trending NFTs data
        """
        response = self._make_request("search/trending")
        # Extract only the NFTs part of the response
        if response and "nfts" in response:
            return {"nfts": response["nfts"]}
        return {"nfts": []}

    def get_global_data(self) -> Dict[str, Any]:
        """
        Get cryptocurrency global data.

        Returns:
            Global market data
        """
        return self._make_request("global")

    def search_coins(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search for coins, categories and markets.

        Args:
            query: Search query

        Returns:
            Search results
        """
        params = {
            "query": query
        }
        return self._make_request("search", params)

    def get_coin_ohlc(self, coin_id: str, vs_currency: str = 'usd', days: int = 7) -> List[List[float]]:
        """
        Get OHLC (Open, High, Low, Close) data for a coin.

        Args:
            coin_id: ID of the coin
            vs_currency: Currency to get market data in
            days: Number of days of data to return (1/7/14/30/90/180/365)

        Returns:
            OHLC data as a list of [timestamp, open, high, low, close]
        """
        params = {
            "vs_currency": vs_currency,
            "days": days
        }
        return self._make_request(f"coins/{coin_id}/ohlc", params)
    
    def get_token_by_contract(
        self, 
        contract_address: str, 
        asset_platform: str = 'ethereum'
    ) -> Dict[str, Any]:
        """
        Get token data by contract address on a specific blockchain platform.
        
        Args:
            contract_address: Contract address of the token
            asset_platform: Asset platform ID (e.g., 'ethereum', 'binance-smart-chain')
            
        Returns:
            Token data
            
        Raises:
            Exception: For API request errors
        """
        endpoint = f"coins/{asset_platform}/contract/{contract_address}"
        params = {
            "tickers": "true",
            "market_data": "true",
            "community_data": "true",
            "developer_data": "true",
            "sparkline": "false"
        }
        
        return self._make_request(endpoint, params)
    
    def get_asset_platforms(self) -> List[Dict[str, Any]]:
        """
        Get a list of all asset platforms (blockchains) supported by CoinGecko.
        
        Returns:
            List of asset platform data
            
        Raises:
            Exception: For API request errors
        """
        return self._make_request("asset_platforms")
    
    def get_supported_vs_currencies(self) -> List[str]:
        """
        Get list of supported vs currencies (fiat currencies used for price conversions).
        
        Returns:
            List of supported currency codes (e.g., 'usd', 'eur', 'btc', etc.)
        """
        return self._make_request("simple/supported_vs_currencies")

    def get_global_defi_data(self) -> Dict[str, Any]:
        """
        Get global decentralized finance (DeFi) data.

        Returns:
            Global DeFi market data
        """
        return self._make_request("global/decentralized_finance_defi")
    
    def get_companies_public_treasury(self, coin_id: str) -> Dict[str, Any]:
        """
        Get public companies holding a specific cryptocurrency in their treasury.

        Args:
            coin_id: ID of the coin (e.g., "bitcoin" or "ethereum")

        Returns:
            Public companies treasury data
        """
        return self._make_request(f"companies/public_treasury/{coin_id}")


# Create a singleton instance for use throughout the app
api = CoinGeckoAPI()
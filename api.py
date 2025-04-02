"""
API module for interacting with the CoinGecko API directly using requests.
"""
import requests
import time
import os
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional

load_dotenv()

class CoinGeckoAPI:
    """Class for direct interaction with the CoinGecko API."""

    COINGECKO_BASE_URL = os.getenv("COINGECKO_BASE_URL")
    if COINGECKO_BASE_URL is None:
        raise ValueError("COINGECKO_BASE_URL not set in environment variables.")
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
        self.rate_limit_wait = 1.5  # Wait at least 1.5s between requests to respect rate limits
    
    def _respect_rate_limit(self):
        """Ensures we don't exceed rate limits by enforcing delays between requests."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.rate_limit_wait:
            time.sleep(self.rate_limit_wait - elapsed)
        
        self.last_request_time = time.time()
    
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
            coin_ids: List of coin IDs (e.g., ['bitcoin', 'ethereum'])
            vs_currencies: List of currencies (e.g., ['usd', 'eur'])
            
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
            order: Sorting criteria
            
        Returns:
            List of coin market data
        """
        params = {
            "vs_currency": vs_currency,
            "per_page": count,
            "page": page,
            "order": order
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
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false"
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
            interval: Data interval (only valid for data up to 90 days,
                      options: daily, hourly, minutely)
            
        Returns:
            Historical price, market cap, and volume data
        """
        params = {
            "vs_currency": vs_currency,
            "days": days
        }
        
        # Only add interval for data up to 90 days
        if days <= 90:
            params["interval"] = interval
            
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
            Historical price, market cap, and volume data
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

# Create a singleton instance for use throughout the app
api = CoinGeckoAPI()
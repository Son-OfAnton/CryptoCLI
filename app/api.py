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
            List of OHLC data points with structure:
            [timestamp, open, high, low, close]
        """
        if days not in [1, 7, 14, 30, 90, 180, 365]:
            raise ValueError(
                "Days parameter must be one of: 1, 7, 14, 30, 90, 180, 365")

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
            Dictionary containing token metadata and market data
            
        Raises:
            ValueError: If asset platform is not supported
            Exception: For API request errors
        """
        # Ensure contract address is valid (basic validation)
        if not contract_address.startswith('0x') or len(contract_address) != 42:
            raise ValueError(
                "Invalid contract address. Must be a valid ERC-20 or similar token address "
                "starting with '0x' and 42 characters long."
            )
        
        # List of common platforms (not comprehensive)
        supported_platforms = [
            'ethereum', 'binance-smart-chain', 'polygon-pos', 'optimistic-ethereum', 
            'arbitrum-one', 'avalanche', 'fantom', 'solana'
        ]
        
        # Validate asset platform (non-exhaustive check)
        if asset_platform not in supported_platforms:
            platform_list = ", ".join(supported_platforms)
            raise ValueError(
                f"Asset platform '{asset_platform}' not recognized. "
                f"Supported platforms include: {platform_list}"
            )
            
        # Make API request
        endpoint = f"coins/{asset_platform}/contract/{contract_address}"
        
        # Additional parameters to get detailed market data and tickers
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

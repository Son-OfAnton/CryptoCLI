"""
Module for retrieving and displaying cryptocurrency price information.
"""
from typing import Dict, List
from rich.table import Table
from rich.console import Console
from .api import api
from .utils.formatting import (
    console, 
    format_currency, 
    format_large_number,
    format_price_change,
    print_error, 
    print_warning
)

def format_price_table(price_data: Dict[str, Dict[str, float]], currencies: List[str]) -> None:
    """
    Format and display price data for multiple cryptocurrencies in a table.
    
    Args:
        price_data: Dictionary with coin IDs as keys and price data as values
        currencies: List of currencies used for prices
    """
    if not price_data:
        print_warning("No price data found for the specified coins.")
        return
    
    table = Table(title="Current Cryptocurrency Prices")
    
    # Add columns for the table
    table.add_column("Coin", style="cyan", justify="left")
    for currency in currencies:
        table.add_column(currency.upper(), justify="right")
    
    # Add rows for each coin
    for coin_id, prices in sorted(price_data.items()):
        row = [coin_id]
        for currency in currencies:
            if currency in prices:
                # Format the price based on the currency
                price = prices[currency]
                if currency.lower() == 'usd':
                    row.append(f"${price:,.2f}")
                elif currency.lower() == 'eur':
                    row.append(f"€{price:,.2f}")
                elif currency.lower() == 'gbp':
                    row.append(f"£{price:,.2f}")
                elif currency.lower() in ['btc', 'eth', 'ltc']:
                    row.append(f"{price:.8f}")
                else:
                    row.append(f"{price:,.4f}")
            else:
                row.append("N/A")
        
        table.add_row(*row)
    
    # Display the table
    console.print(table)

def format_detailed_price_table(price_data: Dict[str, Dict[str, float]], currency: str) -> None:
    """
    Format and display detailed price data with change percentages in a table.
    
    Args:
        price_data: Dictionary with coin IDs as keys and detailed price data as values
        currency: Base currency for price data
    """
    if not price_data:
        print_warning("No price data found for the specified coins.")
        return
    
    table = Table(title=f"Cryptocurrency Prices and Market Data (in {currency.upper()})")
    
    # Define columns
    table.add_column("Rank", justify="right", style="dim")
    table.add_column("Coin", justify="left", style="cyan")
    table.add_column("Symbol", justify="left", style="green")
    table.add_column("Price", justify="right")
    table.add_column("24h Change", justify="right")
    table.add_column("Market Cap", justify="right")
    table.add_column("Volume (24h)", justify="right")
    
    # Prepare data for sorting by rank
    coin_data = []
    for coin_id, data in price_data.items():
        price = data.get(currency, 0)
        price_change = data.get(f"{currency}_24h_change", 0)
        market_cap = data.get(f"{currency}_market_cap", 0)
        volume = data.get(f"{currency}_volume", 0)
        market_cap_rank = data.get("market_cap_rank", 999999)  # Default high rank for sorting
        symbol = data.get("symbol", "").upper()
        name = data.get("name", coin_id)
        
        coin_data.append({
            "id": coin_id,
            "name": name,
            "symbol": symbol,
            "price": price,
            "price_change": price_change,
            "market_cap": market_cap,
            "volume": volume,
            "rank": market_cap_rank
        })
    
    # Sort by market cap rank
    coin_data.sort(key=lambda x: x["rank"])
    
    # Add rows to the table
    for coin in coin_data:
        # Format price based on currency
        if currency.lower() == 'usd':
            price_str = f"${coin['price']:,.2f}"
        elif currency.lower() == 'eur':
            price_str = f"€{coin['price']:,.2f}"
        elif currency.lower() == 'gbp':
            price_str = f"£{coin['price']:,.2f}"
        else:
            price_str = f"{coin['price']:,.4f} {currency.upper()}"
        
        # Add the row with all data
        table.add_row(
            f"#{coin['rank']}" if coin['rank'] != 999999 else "N/A",
            coin['name'],
            coin['symbol'],
            price_str,
            format_price_change(coin['price_change']),
            format_large_number(coin['market_cap']),
            format_large_number(coin['volume'])
        )
    
    # Display the table
    console.print(table)

def get_current_prices(coin_ids: List[str], currencies: List[str], display: bool = True) -> Dict[str, Dict[str, float]]:
    """
    Get current prices for multiple cryptocurrencies.
    
    Args:
        coin_ids: List of coin IDs (e.g., ['bitcoin', 'ethereum'])
        currencies: List of currencies (e.g., ['usd', 'eur'])
        display: Whether to display the results
        
    Returns:
        Dictionary with coin IDs as keys and price data as values
    """
    try:
        # Make API request to get prices
        price_data = api.get_price(coin_ids, currencies)
        
        # Display the results if requested
        if display:
            format_price_table(price_data, currencies)
            
        return price_data
    except Exception as e:
        print_error(f"Failed to fetch price data: {str(e)}")
        return {}

def get_prices_with_change(coin_ids: List[str], vs_currency: str = 'usd') -> Dict[str, Dict[str, float]]:
    """
    Get current prices for multiple cryptocurrencies with price change percentages.
    
    Args:
        coin_ids: List of coin IDs (e.g., ['bitcoin', 'ethereum'])
        vs_currency: Currency to get price data in
        
    Returns:
        Dictionary with detailed price information including change percentages
    """
    try:
        # For price change data, we need to use the markets endpoint
        # This gives us price change percentages which aren't available in the simple price endpoint
        markets_data = api.get_coin_markets(
            vs_currency=vs_currency,
            count=len(coin_ids) if len(coin_ids) <= 250 else 250,  # API limit
            page=1
        )
        
        # Filter to only get the requested coins
        requested_coins = set(coin_ids)
        filtered_data = [coin for coin in markets_data if coin['id'] in requested_coins]
        
        # Ensure all requested coins are included by checking which ones are missing
        found_coins = {coin['id'] for coin in filtered_data}
        missing_coins = requested_coins - found_coins
        
        if missing_coins:
            console.print(f"[yellow]Warning:[/yellow] Could not find detailed data for: {', '.join(missing_coins)}")
        
        # Transform to a similar format as the simple price endpoint but with more details
        result = {}
        for coin in filtered_data:
            result[coin['id']] = {
                vs_currency: coin['current_price'],
                f"{vs_currency}_24h_change": coin.get('price_change_percentage_24h', 0),
                f"{vs_currency}_market_cap": coin.get('market_cap', 0),
                f"{vs_currency}_volume": coin.get('total_volume', 0),
                "market_cap_rank": coin.get('market_cap_rank', 0),
                "symbol": coin.get('symbol', ''),
                "name": coin.get('name', coin['id'])
            }
        
        # Display the results in a table
        format_detailed_price_table(result, vs_currency)
            
        return result
    except Exception as e:
        print_error(f"Failed to fetch detailed price data: {str(e)}")
        return {}
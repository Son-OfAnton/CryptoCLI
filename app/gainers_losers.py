"""
Module for retrieving and displaying top cryptocurrency gainers and losers by price change.
"""
from typing import Dict, List, Any, Optional, Tuple, Literal
import json
from datetime import datetime
import os
from rich.table import Table
from rich.panel import Panel
from rich.console import Console

from app.api import api
from app.utils.formatting import (
    console,
    print_error,
    print_warning,
    print_success,
    format_currency,
    format_large_number,
    format_price_change
)

# Define time period types
TimePeriod = Literal["1h", "24h", "7d", "14d", "30d", "200d", "1y"]

# Mapping of time periods to CoinGecko API parameters
TIME_PERIOD_MAP = {
    "1h": "price_change_percentage_1h_in_currency",
    "24h": "price_change_percentage_24h_in_currency",
    "7d": "price_change_percentage_7d_in_currency",
    "14d": "price_change_percentage_14d_in_currency",
    "30d": "price_change_percentage_30d_in_currency",
    "200d": "price_change_percentage_200d_in_currency",
    "1y": "price_change_percentage_1y_in_currency"
}

# Human-readable period descriptions
TIME_PERIOD_DESCRIPTIONS = {
    "1h": "1 hour",
    "24h": "24 hours",
    "7d": "7 days",
    "14d": "14 days",
    "30d": "30 days",
    "200d": "200 days",
    "1y": "1 year"
}

def get_coin_market_data(
    vs_currency: str = 'usd',
    count: int = 250,
    time_periods: List[TimePeriod] = ["1h", "24h", "7d"],
    page: int = 1
) -> List[Dict[str, Any]]:
    """
    Get comprehensive coin market data including price change percentages.
    
    Args:
        vs_currency: Currency for market data (e.g., 'usd', 'eur')
        count: Number of coins to fetch (max 250 per page)
        time_periods: List of time periods for price change percentages
        page: Page number for pagination
        
    Returns:
        List of coin market data
    """
    # Convert list of time periods to comma-separated string for CoinGecko API
    price_change_percentage = ','.join(time_periods)
    
    try:
        # Get coin market data with specified price change percentages
        params = {
            "vs_currency": vs_currency,
            "per_page": count,
            "page": page,
            "sparkline": "false",
            "price_change_percentage": price_change_percentage
        }
        endpoint = "coins/markets"
        
        # Make the API request
        response = api._make_request(endpoint, params)
        
        return response
    except Exception as e:
        print_error(f"Failed to get coin market data: {str(e)}")
        return []

def get_gainers_losers(
    time_period: TimePeriod = "24h",
    vs_currency: str = 'usd',
    limit: int = 30,
    display: bool = True,
    save: bool = False,
    output: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Get top cryptocurrency gainers and losers for a specific time period.
    
    Args:
        time_period: Time period for price change ('1h', '24h', '7d', '14d', '30d', '200d', '1y')
        vs_currency: Currency to display prices in (e.g., 'usd', 'eur')
        limit: Maximum number of gainers and losers to display
        display: Whether to display the data in the console
        save: Whether to save the data to a JSON file
        output: Optional filename to save data to
        
    Returns:
        Tuple containing lists of top gainers and losers
    """
    # Ensure a valid time period
    if time_period not in TIME_PERIOD_MAP:
        print_error(f"Invalid time period: {time_period}. Please choose from {', '.join(TIME_PERIOD_MAP.keys())}")
        return [], []
    
    # Fetch coin market data with price change percentages
    market_data = get_coin_market_data(
        vs_currency=vs_currency,
        count=250,  # Get a good amount of coins to find top gainers and losers
        time_periods=[time_period],
        page=1
    )
    
    if not market_data:
        print_error(f"No market data available")
        return [], []
    
    # Get the price change percentage field name for the specified time period
    price_change_field = TIME_PERIOD_MAP[time_period]
    
    # Filter out coins with no price change data for the specified period
    valid_coins = [
        coin for coin in market_data 
        if price_change_field in coin and coin[price_change_field] is not None
    ]
    
    if not valid_coins:
        print_error(f"No price change data available for {TIME_PERIOD_DESCRIPTIONS[time_period]}")
        return [], []
    
    # Sort coins by price change percentage
    sorted_by_change = sorted(
        valid_coins, 
        key=lambda x: x[price_change_field], 
        reverse=True
    )
    
    # Get top gainers and losers
    gainers = sorted_by_change[:limit]
    losers = sorted_by_change[-limit:][::-1]  # Reverse to show biggest losers first
    
    # Display if requested
    if display:
        display_gainers_losers(gainers, losers, time_period, vs_currency)
    
    # Save if requested
    if save:
        save_gainers_losers_data(gainers, losers, time_period, vs_currency, output)
    
    return gainers, losers

def display_gainers_losers(
    gainers: List[Dict[str, Any]],
    losers: List[Dict[str, Any]],
    time_period: TimePeriod,
    vs_currency: str
):
    """
    Display the top gainers and losers in a formatted table.
    
    Args:
        gainers: List of top gaining coins
        losers: List of top losing coins
        time_period: Time period for the price change
        vs_currency: Currency used for pricing
    """
    # Get the price change field name for the time period
    price_change_field = TIME_PERIOD_MAP[time_period]
    period_description = TIME_PERIOD_DESCRIPTIONS[time_period]
    
    # Create gainers table
    gainers_table = Table(
        title=f"🚀 Top Gainers (Last {period_description})",
        show_header=True,
        header_style="bold green"
    )
    
    # Add columns
    gainers_table.add_column("#", style="dim", width=3, justify="right")
    gainers_table.add_column("Coin", style="cyan", justify="left")
    gainers_table.add_column("Symbol", style="blue", justify="center")
    gainers_table.add_column(f"Price ({vs_currency.upper()})", justify="right")
    gainers_table.add_column(f"Change ({period_description})", justify="right")
    gainers_table.add_column("Market Cap", justify="right")
    gainers_table.add_column("Volume (24h)", justify="right")
    
    # Add rows for gainers
    for i, coin in enumerate(gainers, 1):
        # Get the price change percentage value and format it
        change_value = coin.get(price_change_field, 0)
        change_formatted = format_price_change(change_value)
        
        gainers_table.add_row(
            str(i),
            coin.get('name', 'Unknown'),
            coin.get('symbol', 'N/A').upper(),
            format_currency(coin.get('current_price', 0), vs_currency),
            str(change_formatted),
            format_large_number(coin.get('market_cap', 0)),
            format_large_number(coin.get('total_volume', 0))
        )
    
    # Create losers table
    losers_table = Table(
        title=f"📉 Top Losers (Last {period_description})",
        show_header=True,
        header_style="bold red"
    )
    
    # Add columns (same as gainers)
    losers_table.add_column("#", style="dim", width=3, justify="right")
    losers_table.add_column("Coin", style="cyan", justify="left")
    losers_table.add_column("Symbol", style="blue", justify="center")
    losers_table.add_column(f"Price ({vs_currency.upper()})", justify="right")
    losers_table.add_column(f"Change ({period_description})", justify="right")
    losers_table.add_column("Market Cap", justify="right") 
    losers_table.add_column("Volume (24h)", justify="right")
    
    # Add rows for losers
    for i, coin in enumerate(losers, 1):
        # Get the price change percentage value and format it
        change_value = coin.get(price_change_field, 0)
        change_formatted = format_price_change(change_value)
        
        losers_table.add_row(
            str(i),
            coin.get('name', 'Unknown'),
            coin.get('symbol', 'N/A').upper(),
            format_currency(coin.get('current_price', 0), vs_currency),
            str(change_formatted),
            format_large_number(coin.get('market_cap', 0)),
            format_large_number(coin.get('total_volume', 0))
        )
    
    # Print the tables
    console.print(gainers_table)
    console.print("")  # Add a blank line between tables
    console.print(losers_table)
    
    # Add timestamp
    console.print(f"\n[dim]Data retrieved at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")

def save_gainers_losers_data(
    gainers: List[Dict[str, Any]],
    losers: List[Dict[str, Any]],
    time_period: TimePeriod,
    vs_currency: str,
    filename: Optional[str] = None
) -> str:
    """
    Save gainers and losers data to a JSON file.
    
    Args:
        gainers: List of top gaining coins
        losers: List of top losing coins
        time_period: Time period for the price change
        vs_currency: Currency used for pricing
        filename: Optional custom filename
        
    Returns:
        Path to the saved file
    """
    # Create data structure
    data = {
        "time_period": time_period,
        "period_description": TIME_PERIOD_DESCRIPTIONS[time_period],
        "vs_currency": vs_currency,
        "timestamp": datetime.now().isoformat(),
        "gainers": gainers,
        "losers": losers
    }
    
    # Generate filename if not provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        period_text = time_period.replace('/', '_')
        filename = f"gainers_losers_{period_text}_{vs_currency}_{timestamp}.json"
    
    # Ensure filename has .json extension
    if not filename.endswith('.json'):
        filename += '.json'
    
    # Save to file
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    
    # Get absolute path
    file_path = os.path.abspath(filename)
    
    # Print success message
    print_success(f"Gainers and losers data saved to: {file_path}")
    
    return file_path
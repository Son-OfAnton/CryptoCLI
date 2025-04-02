"""
Module for retrieving and displaying historical cryptocurrency price data.
"""
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
import time
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import json

from .api import api
from .utils.formatting import (
    console, 
    format_currency, 
    format_price_change,
    format_timestamp,
    print_error, 
    print_warning
)

# Time period constants
DAY = 1
WEEK = 7
MONTH = 30
YEAR = 365

def get_date_range(days: int) -> Tuple[int, int]:
    """
    Calculate the date range to fetch historical data.
    
    Args:
        days: Number of days to look back
        
    Returns:
        Tuple of (from_timestamp, to_timestamp) in Unix time
    """
    to_datetime = datetime.now()
    from_datetime = to_datetime - timedelta(days=days)
    
    # Convert to Unix timestamp in seconds
    from_timestamp = int(from_datetime.timestamp())
    to_timestamp = int(to_datetime.timestamp())
    
    return (from_timestamp, to_timestamp)

def get_historical_prices(
    coin_id: str, 
    vs_currency: str = 'usd', 
    days: int = WEEK,
    display: bool = True
) -> Dict[str, Any]:
    """
    Get historical price data for a cryptocurrency for the specified time period.
    
    Args:
        coin_id: ID of the cryptocurrency (e.g., 'bitcoin')
        vs_currency: Currency to get prices in (e.g., 'usd')
        days: Number of days to look back
        display: Whether to display the results
        
    Returns:
        Dictionary with historical price data
    """
    try:
        # Make API request to get historical prices
        market_data = api.get_coin_market_chart(
            coin_id=coin_id,
            vs_currency=vs_currency,
            days=days
        )
        
        if not market_data or "prices" not in market_data or not market_data["prices"]:
            print_warning(f"No historical data found for {coin_id} in the last {days} days.")
            return {}
        
        # Process the data
        historical_data = {
            "coin_id": coin_id,
            "currency": vs_currency,
            "days": days,
            "prices": market_data.get("prices", []),
            "market_caps": market_data.get("market_caps", []),
            "total_volumes": market_data.get("total_volumes", [])
        }
        
        # Get the price change percentage
        if historical_data["prices"]:
            first_price = historical_data["prices"][0][1]
            last_price = historical_data["prices"][-1][1]
            price_change = ((last_price - first_price) / first_price) * 100
            historical_data["price_change_percentage"] = price_change
        else:
            historical_data["price_change_percentage"] = 0
            
        # Display results if requested
        if display:
            display_historical_data(historical_data)
            
        return historical_data
    except Exception as e:
        print_error(f"Failed to fetch historical data: {str(e)}")
        return {}

def display_historical_data(data: Dict[str, Any]) -> None:
    """
    Display historical price data in the console.
    
    Args:
        data: Dictionary with historical price data
    """
    if not data or "prices" not in data or not data["prices"]:
        print_warning("No historical data to display.")
        return
    
    coin_id = data["coin_id"]
    currency = data["currency"].upper()
    days = data["days"]
    
    # Get time period description
    if days == DAY:
        time_period = "24 hours"
    elif days == WEEK:
        time_period = "7 days"
    elif days == MONTH:
        time_period = "30 days"
    elif days == YEAR:
        time_period = "1 year"
    else:
        time_period = f"{days} days"
    
    # Create a table for price summary
    table = Table(title=f"Historical Data for {coin_id.capitalize()} ({currency}) - {time_period}")
    
    # Add columns
    table.add_column("Metric", style="cyan", justify="left")
    table.add_column("Value", justify="right")
    
    # Get price data
    prices = data["prices"]
    
    # Calculate metrics
    current_price = prices[-1][1]
    start_price = prices[0][1]
    price_change = data.get("price_change_percentage", 0)
    price_high = max(price[1] for price in prices)
    price_low = min(price[1] for price in prices)
    
    # Format the timestamps
    start_date = datetime.fromtimestamp(prices[0][0] / 1000).strftime('%Y-%m-%d %H:%M:%S')
    end_date = datetime.fromtimestamp(prices[-1][0] / 1000).strftime('%Y-%m-%d %H:%M:%S')
    
    # Add rows to the table
    table.add_row("Start Date", start_date)
    table.add_row("End Date", end_date)
    table.add_row("Start Price", format_currency(start_price, currency.lower()))
    table.add_row("Current Price", format_currency(current_price, currency.lower()))
    table.add_row("Price Change", format_price_change(price_change))
    table.add_row("Highest Price", format_currency(price_high, currency.lower()))
    table.add_row("Lowest Price", format_currency(price_low, currency.lower()))
    
    # Display the table
    console.print(table)
    
    # Print a note about data points
    console.print(f"[dim]Note: Data includes {len(prices)} price points over {time_period}.[/dim]\n")
    
    # Get some insights from the data
    console.print("[bold]Market Insights:[/bold]")
    
    if price_change > 0:
        console.print(f"✅ [green]{coin_id.capitalize()} has risen by {format_price_change(price_change)} over the past {time_period}.[/green]")
    elif price_change < 0:
        console.print(f"❌ [red]{coin_id.capitalize()} has declined by {format_price_change(abs(price_change))} over the past {time_period}.[/red]")
    else:
        console.print(f"➡️ {coin_id.capitalize()} has remained stable over the past {time_period}.")
    
    # Add volatility information
    price_range_percent = ((price_high - price_low) / price_low) * 100
    if price_range_percent > 20:
        console.print(f"⚠️ High volatility: Price fluctuated by {price_range_percent:.2f}% during this period.")
    elif price_range_percent > 10:
        console.print(f"📊 Moderate volatility: Price fluctuated by {price_range_percent:.2f}% during this period.")
    else:
        console.print(f"🔒 Low volatility: Price fluctuated by only {price_range_percent:.2f}% during this period.")

def save_historical_data(data: Dict[str, Any], filename: Optional[str] = None) -> str:
    """
    Save historical data to a JSON file.
    
    Args:
        data: Dictionary with historical price data
        filename: Optional filename to save to
        
    Returns:
        Path to the saved file
    """
    if not data:
        print_error("No data to save.")
        return ""
        
    # Generate a default filename if none provided
    if not filename:
        coin_id = data.get("coin_id", "crypto")
        currency = data.get("currency", "usd")
        timestamp = int(time.time())
        filename = f"{coin_id}_{currency}_{timestamp}.json"
    
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
            
        print_warning(f"Historical data saved to {filename}")
        return filename
    except Exception as e:
        print_error(f"Failed to save data: {str(e)}")
        return ""
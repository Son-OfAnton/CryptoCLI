"""
Module for retrieving and displaying OHLC (Open, High, Low, Close) chart data within a timestamp range.
"""
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import time
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.box import Box, MINIMAL
import json
import os

from app.api import api
from app.utils.formatting import (
    console,
    format_currency,
    format_price_change,
    format_timestamp,
    print_error,
    print_warning,
    print_success
)

# Import display functions from original OHLC module
from app.ohlc import display_ohlc_summary, display_ascii_chart

def get_ohlc_range_data(
    coin_id: str,
    vs_currency: str = 'usd',
    from_timestamp: int = None,
    to_timestamp: int = None,
    display: bool = True
) -> List[List[float]]:
    """
    Get OHLC (Open, High, Low, Close) data for a cryptocurrency within a specific timestamp range.
    
    Args:
        coin_id: ID of the cryptocurrency (e.g., 'bitcoin')
        vs_currency: Currency to get data in (e.g., 'usd')
        from_timestamp: Starting timestamp (Unix timestamp in seconds)
        to_timestamp: Ending timestamp (Unix timestamp in seconds)
        display: Whether to display the results
        
    Returns:
        List of OHLC data points with structure: [timestamp, open, high, low, close]
    """
    try:
        # Validate timestamps
        current_time = int(time.time())
        
        # If from_timestamp is not provided, default to 30 days ago
        if from_timestamp is None:
            from_timestamp = current_time - (30 * 24 * 60 * 60)  # 30 days ago
            
        # If to_timestamp is not provided, default to current time
        if to_timestamp is None:
            to_timestamp = current_time
            
        # Ensure timestamps are in the correct order
        if from_timestamp > to_timestamp:
            print_warning("Start timestamp is after end timestamp. Swapping values.")
            from_timestamp, to_timestamp = to_timestamp, from_timestamp
            
        # Ensure the range is not too large (CoinGecko may have limits)
        max_range = 90 * 24 * 60 * 60  # 90 days in seconds
        if to_timestamp - from_timestamp > max_range:
            print_warning(f"Requested range is very large (> 90 days). This may result in a large amount of data or API limitations.")
            
        # Make API request to get OHLC data within the range
        # Note: CoinGecko doesn't directly support OHLC with from-to range, 
        # so we need to use the market chart range endpoint and transform the data
        market_data = api.get_coin_market_chart_range(
            coin_id=coin_id,
            vs_currency=vs_currency,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp
        )
        
        if not market_data:
            print_warning(f"No market data found for {coin_id} in the specified range.")
            return []
            
        # Extract prices for OHLC calculation
        prices = market_data.get('prices', [])
        if not prices or len(prices) == 0:
            print_warning(f"No price data found for {coin_id} in the specified range.")
            return []
            
        # Transform price data to OHLC format
        # Group prices by day to calculate OHLC for each day
        daily_prices = {}
        
        for price_point in prices:
            timestamp = price_point[0]  # Timestamp in milliseconds
            price = price_point[1]
            
            # Convert to date string (YYYY-MM-DD) for grouping by day
            date_str = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d')
            
            if date_str not in daily_prices:
                daily_prices[date_str] = []
                
            daily_prices[date_str].append((timestamp, price))
            
        # Calculate OHLC for each day
        ohlc_data = []
        
        for date_str, day_prices in daily_prices.items():
            if len(day_prices) == 0:
                continue
                
            # Sort by timestamp
            day_prices.sort(key=lambda x: x[0])
            
            # Get first timestamp of the day for OHLC timestamp
            timestamp = day_prices[0][0]
            
            # Calculate open, high, low, close
            open_price = day_prices[0][1]
            close_price = day_prices[-1][1]
            high_price = max(price for _, price in day_prices)
            low_price = min(price for _, price in day_prices)
            
            # Create OHLC data point
            ohlc_data.append([timestamp, open_price, high_price, low_price, close_price])
            
        if not ohlc_data or len(ohlc_data) == 0:
            print_warning(f"Could not calculate OHLC data for {coin_id} in the specified range.")
            return []
        
        # Display results if requested
        if display:
            display_ohlc_range_data(ohlc_data, coin_id, vs_currency, from_timestamp, to_timestamp)
            
        return ohlc_data
    except Exception as e:
        print_error(f"Failed to fetch OHLC range data: {str(e)}")
        return []

def display_ohlc_range_data(
    ohlc_data: List[List[float]],
    coin_id: str,
    vs_currency: str,
    from_timestamp: int,
    to_timestamp: int
) -> None:
    """
    Display OHLC data for a specific timestamp range in a tabular format.
    
    Args:
        ohlc_data: List of OHLC data points
        coin_id: ID of the cryptocurrency
        vs_currency: Currency used for the data
        from_timestamp: Starting timestamp (Unix timestamp in seconds)
        to_timestamp: Ending timestamp (Unix timestamp in seconds)
    """
    if not ohlc_data or len(ohlc_data) == 0:
        print_warning("No OHLC data to display.")
        return
    
    # Format timestamps for display
    from_date = datetime.fromtimestamp(from_timestamp).strftime('%Y-%m-%d')
    to_date = datetime.fromtimestamp(to_timestamp).strftime('%Y-%m-%d')
    
    # Create a table for OHLC data
    title_text = f"OHLC Data for {coin_id.capitalize()} ({vs_currency.upper()}) - {from_date} to {to_date}"
    table = Table(title=title_text, box=MINIMAL)
    
    # Add columns for the table
    table.add_column("Date", style="cyan", justify="left")
    table.add_column("Open", justify="right")
    table.add_column("High", justify="right")
    table.add_column("Low", justify="right")
    table.add_column("Close", justify="right")
    table.add_column("Change %", justify="right")
    
    # Process data for display
    formatted_rows = []
    for data_point in ohlc_data:
        timestamp = data_point[0]
        open_price = data_point[1]
        high_price = data_point[2]
        low_price = data_point[3]
        close_price = data_point[4]
        
        # Calculate percentage change
        price_change = ((close_price - open_price) / open_price) * 100
        
        # Format date
        date_str = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d')
        
        # Format prices
        open_str = format_currency(open_price, vs_currency)
        high_str = format_currency(high_price, vs_currency)
        low_str = format_currency(low_price, vs_currency)
        close_str = format_currency(close_price, vs_currency)
        change_str = format_price_change(price_change)
        
        # Add to formatted rows
        formatted_rows.append((date_str, open_str, high_str, low_str, close_str, change_str))
    
    # Sort rows by date (oldest to newest)
    formatted_rows.sort(key=lambda x: x[0])
    
    # Add rows to the table
    for row in formatted_rows:
        table.add_row(*row)
    
    # Display the table
    console.print(table)
    
    # Calculate and display summary statistics
    display_ohlc_summary(ohlc_data, coin_id, vs_currency)
    
    # Display ASCII chart if possible
    display_ascii_chart(ohlc_data, coin_id, vs_currency)

def save_ohlc_range_data(
    ohlc_data: List[List[float]],
    coin_id: str,
    vs_currency: str,
    from_timestamp: int,
    to_timestamp: int,
    filename: Optional[str] = None
) -> str:
    """
    Save OHLC range data to a JSON file.
    
    Args:
        ohlc_data: List of OHLC data points
        coin_id: ID of the cryptocurrency
        vs_currency: Currency used for the data
        from_timestamp: Starting timestamp (Unix timestamp in seconds)
        to_timestamp: Ending timestamp (Unix timestamp in seconds)
        filename: Optional filename to save to
        
    Returns:
        Path to the saved file
    """
    if not ohlc_data or len(ohlc_data) == 0:
        print_error("No data to save.")
        return ""
        
    # Generate a default filename if none provided
    if not filename:
        current_timestamp = int(time.time())
        from_date = datetime.fromtimestamp(from_timestamp).strftime('%Y%m%d')
        to_date = datetime.fromtimestamp(to_timestamp).strftime('%Y%m%d')
        filename = f"{coin_id}_{vs_currency}_ohlc_range_{from_date}_to_{to_date}_{current_timestamp}.json"
    
    try:
        # Convert the data to a more readable format
        formatted_data = []
        
        for point in ohlc_data:
            timestamp = point[0]
            date_str = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
            
            formatted_point = {
                "timestamp": timestamp,
                "date": date_str,
                "open": point[1],
                "high": point[2],
                "low": point[3],
                "close": point[4]
            }
            
            formatted_data.append(formatted_point)
        
        # Create a data object with metadata
        data_object = {
            "coin_id": coin_id,
            "currency": vs_currency,
            "from_timestamp": from_timestamp,
            "to_timestamp": to_timestamp,
            "from_date": datetime.fromtimestamp(from_timestamp).strftime('%Y-%m-%d'),
            "to_date": datetime.fromtimestamp(to_timestamp).strftime('%Y-%m-%d'),
            "data_points": len(ohlc_data),
            "generated_at": int(time.time()),
            "ohlc_data": formatted_data
        }
        
        # Write to file
        with open(filename, 'w') as f:
            json.dump(data_object, f, indent=4)
            
        print_success(f"OHLC range data saved to {filename}")
        return filename
    except Exception as e:
        print_error(f"Failed to save OHLC range data: {str(e)}")
        return ""
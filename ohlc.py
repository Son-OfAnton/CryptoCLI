"""
Module for retrieving and displaying OHLC (Open, High, Low, Close) chart data.
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

from .api import api
from .utils.formatting import (
    console,
    format_currency,
    format_price_change,
    format_timestamp,
    print_error,
    print_warning,
    print_success
)

# Valid time periods for OHLC data
VALID_DAYS = [1, 7, 14, 30, 90, 180, 365]

def get_ohlc_data(
    coin_id: str,
    vs_currency: str = 'usd',
    days: int = 7,
    display: bool = True
) -> List[List[float]]:
    """
    Get OHLC (Open, High, Low, Close) data for a cryptocurrency.
    
    Args:
        coin_id: ID of the cryptocurrency (e.g., 'bitcoin')
        vs_currency: Currency to get data in (e.g., 'usd')
        days: Number of days of data (1/7/14/30/90/180/365)
        display: Whether to display the results
        
    Returns:
        List of OHLC data points with structure: [timestamp, open, high, low, close]
    """
    try:
        # Validate days parameter
        if days not in VALID_DAYS:
            days_str = ", ".join(str(d) for d in VALID_DAYS)
            print_warning(f"Invalid days parameter. Using default (7). Valid values: {days_str}")
            days = 7
            
        # Make API request to get OHLC data
        ohlc_data = api.get_coin_ohlc(
            coin_id=coin_id,
            vs_currency=vs_currency,
            days=days
        )
        
        if not ohlc_data or len(ohlc_data) == 0:
            print_warning(f"No OHLC data found for {coin_id} in the last {days} days.")
            return []
        
        # Display results if requested
        if display:
            display_ohlc_data(ohlc_data, coin_id, vs_currency, days)
            
        return ohlc_data
    except Exception as e:
        print_error(f"Failed to fetch OHLC data: {str(e)}")
        return []

def display_ohlc_data(
    ohlc_data: List[List[float]],
    coin_id: str,
    vs_currency: str,
    days: int
) -> None:
    """
    Display OHLC data in a tabular format.
    
    Args:
        ohlc_data: List of OHLC data points
        coin_id: ID of the cryptocurrency
        vs_currency: Currency used for the data
        days: Number of days of data
    """
    if not ohlc_data or len(ohlc_data) == 0:
        print_warning("No OHLC data to display.")
        return
    
    # Create a table for OHLC data
    title_text = f"OHLC Data for {coin_id.capitalize()} ({vs_currency.upper()}) - {days} days"
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
        date_str = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M')
        
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

def display_ohlc_summary(
    ohlc_data: List[List[float]],
    coin_id: str,
    vs_currency: str
) -> None:
    """
    Display summary statistics for the OHLC data.
    
    Args:
        ohlc_data: List of OHLC data points
        coin_id: ID of the cryptocurrency
        vs_currency: Currency used for the data
    """
    if not ohlc_data or len(ohlc_data) == 0:
        return
    
    # Extract prices
    opens = [point[1] for point in ohlc_data]
    highs = [point[2] for point in ohlc_data]
    lows = [point[3] for point in ohlc_data]
    closes = [point[4] for point in ohlc_data]
    
    # Calculate statistics
    avg_open = sum(opens) / len(opens)
    avg_close = sum(closes) / len(closes)
    highest = max(highs)
    lowest = min(lows)
    price_range = highest - lowest
    price_range_pct = (price_range / lowest) * 100
    
    # Get first and last data points
    first_point = min(ohlc_data, key=lambda x: x[0])
    last_point = max(ohlc_data, key=lambda x: x[0])
    
    # Calculate overall change
    overall_change = ((last_point[4] - first_point[1]) / first_point[1]) * 100
    
    # Create a summary table
    summary = Table(title="OHLC Summary", box=MINIMAL)
    
    # Add columns
    summary.add_column("Metric", style="cyan", justify="left")
    summary.add_column("Value", justify="right")
    
    # Add rows
    summary.add_row("Starting Price", format_currency(first_point[1], vs_currency))
    summary.add_row("Ending Price", format_currency(last_point[4], vs_currency))
    summary.add_row("Highest Price", format_currency(highest, vs_currency))
    summary.add_row("Lowest Price", format_currency(lowest, vs_currency))
    summary.add_row("Average Open", format_currency(avg_open, vs_currency))
    summary.add_row("Average Close", format_currency(avg_close, vs_currency))
    summary.add_row("Price Range", format_currency(price_range, vs_currency))
    summary.add_row("Price Range %", f"{price_range_pct:.2f}%")
    summary.add_row("Overall Change", format_price_change(overall_change))
    
    # Display the summary
    console.print(summary)

def display_ascii_chart(
    ohlc_data: List[List[float]],
    coin_id: str,
    vs_currency: str,
    width: int = 60,
    height: int = 15
) -> None:
    """
    Display an ASCII chart of the closing prices.
    
    Args:
        ohlc_data: List of OHLC data points
        coin_id: ID of the cryptocurrency
        vs_currency: Currency used for the data
        width: Width of the chart in characters
        height: Height of the chart in characters
    """
    if not ohlc_data or len(ohlc_data) == 0:
        return
    
    # Sort data by timestamp
    sorted_data = sorted(ohlc_data, key=lambda x: x[0])
    
    # Extract closing prices and timestamps
    timestamps = [point[0] for point in sorted_data]
    close_prices = [point[4] for point in sorted_data]
    
    # Find min and max for scaling
    min_price = min(close_prices)
    max_price = max(close_prices)
    price_range = max_price - min_price
    
    # Avoid division by zero
    if price_range == 0:
        price_range = 1
    
    # Create the chart
    chart = []
    
    # Create header
    chart.append(f"Price Chart for {coin_id.capitalize()} ({vs_currency.upper()})")
    chart.append(f"Range: {format_currency(min_price, vs_currency)} - {format_currency(max_price, vs_currency)}")
    chart.append("")
    
    # Create y-axis labels
    y_labels = []
    for i in range(height):
        # Calculate price at this height
        price = max_price - (i * price_range / (height - 1))
        # Format the label
        label = format_currency(price, vs_currency)
        # Add to labels
        y_labels.append(label)
    
    # Calculate x positions for each data point
    num_points = len(close_prices)
    x_positions = []
    
    for i in range(num_points):
        # Calculate position along the width
        pos = int((i / (num_points - 1)) * (width - 1)) if num_points > 1 else 0
        x_positions.append(pos)
    
    # Calculate y positions for each data point
    y_positions = []
    
    for price in close_prices:
        # Scale the price to chart height
        pos = int(((max_price - price) / price_range) * (height - 1)) if price_range > 0 else 0
        y_positions.append(pos)
    
    # Create the chart grid with spaces
    grid = [[' ' for _ in range(width)] for _ in range(height)]
    
    # Plot the line
    for i in range(num_points):
        x = x_positions[i]
        y = y_positions[i]
        
        # Ensure we're within bounds
        if 0 <= y < height and 0 <= x < width:
            grid[y][x] = '●'
    
    # Connect points with lines
    for i in range(1, num_points):
        x1, y1 = x_positions[i-1], y_positions[i-1]
        x2, y2 = x_positions[i], y_positions[i]
        
        # Draw a line between the points
        if x1 == x2:
            # Vertical line
            start, end = min(y1, y2), max(y1, y2)
            for y in range(start + 1, end):
                if 0 <= y < height and 0 <= x1 < width:
                    if grid[y][x1] == ' ':
                        grid[y][x1] = '│'
        elif y1 == y2:
            # Horizontal line
            start, end = min(x1, x2), max(x1, x2)
            for x in range(start + 1, end):
                if 0 <= y1 < height and 0 <= x < width:
                    if grid[y1][x] == ' ':
                        grid[y1][x] = '─'
        else:
            # Diagonal line
            dx = abs(x2 - x1)
            dy = abs(y2 - y1)
            sx = 1 if x1 < x2 else -1
            sy = 1 if y1 < y2 else -1
            err = dx - dy
            
            while (x1 != x2 or y1 != y2):
                if 0 <= y1 < height and 0 <= x1 < width:
                    if grid[y1][x1] == ' ':
                        # Choose the appropriate character for diagonal lines
                        if (sx > 0 and sy < 0) or (sx < 0 and sy > 0):
                            grid[y1][x1] = '/'
                        else:
                            grid[y1][x1] = '\\'
                
                e2 = 2 * err
                if e2 > -dy:
                    err -= dy
                    x1 += sx
                if e2 < dx:
                    err += dx
                    y1 += sy
    
    # Convert grid to strings and add y-axis labels
    for i, row in enumerate(grid):
        label_str = y_labels[i].ljust(10)  # Pad the label to a fixed width
        line = label_str + ''.join(row)
        chart.append(line)
    
    # Add x-axis with timestamps
    chart.append('-' * (width + 10))  # Line under the chart
    
    # Add x-axis labels (just a few to avoid clutter)
    label_indices = [0, num_points // 2, num_points - 1] if num_points > 2 else [0]
    x_labels = []
    
    for idx in label_indices:
        # Format the date
        date_str = datetime.fromtimestamp(timestamps[idx] / 1000).strftime('%m-%d')
        # Calculate position
        pos = x_positions[idx] + 10  # Add offset for y-axis labels
        # Add to labels with position
        x_labels.append((pos, date_str))
    
    # Create x-axis label line
    x_label_line = ' ' * (width + 10)
    for pos, label in x_labels:
        # Place the label at the correct position
        start = max(0, pos - len(label) // 2)
        end = min(len(x_label_line), start + len(label))
        x_label_line = x_label_line[:start] + label[:end-start] + x_label_line[end:]
    
    chart.append(x_label_line)
    
    # Display the chart
    console.print('\n'.join(chart))
    console.print("")  # Add empty line at the end

def save_ohlc_data(
    ohlc_data: List[List[float]],
    coin_id: str,
    vs_currency: str,
    days: int,
    filename: Optional[str] = None
) -> str:
    """
    Save OHLC data to a JSON file.
    
    Args:
        ohlc_data: List of OHLC data points
        coin_id: ID of the cryptocurrency
        vs_currency: Currency used for the data
        days: Number of days of data
        filename: Optional filename to save to
        
    Returns:
        Path to the saved file
    """
    if not ohlc_data or len(ohlc_data) == 0:
        print_error("No data to save.")
        return ""
        
    # Generate a default filename if none provided
    if not filename:
        timestamp = int(time.time())
        filename = f"{coin_id}_{vs_currency}_ohlc_{days}d_{timestamp}.json"
    
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
            "days": days,
            "data_points": len(ohlc_data),
            "generated_at": int(time.time()),
            "ohlc_data": formatted_data
        }
        
        # Write to file
        with open(filename, 'w') as f:
            json.dump(data_object, f, indent=4)
            
        print_success(f"OHLC data saved to {filename}")
        return filename
    except Exception as e:
        print_error(f"Failed to save OHLC data: {str(e)}")
        return ""
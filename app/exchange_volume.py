"""
Module for retrieving and displaying historical volume data for cryptocurrency exchanges.
"""
from typing import Dict, List, Any, Optional, Tuple
import json
import os
from datetime import datetime, timedelta
import time
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.box import ROUNDED
from rich.progress import Progress, TextColumn, BarColumn, SpinnerColumn
import statistics

from app.api import api
from app.utils.formatting import (
    console,
    print_error,
    print_warning,
    print_success,
    format_large_number
)

# Reuse ASCII chart function from OHLC module if available, otherwise define here
try:
    from app.ohlc import display_ascii_chart
except ImportError:
    # Define a simpler version if not available
    def display_ascii_chart(data_points, title, width=60, height=15):
        pass

def get_exchange_volume_history(
    exchange_id: str,
    days: int = 30,
    display: bool = True,
    save: bool = False,
    output: Optional[str] = None
) -> List[List[float]]:
    """
    Get historical trading volume data for a cryptocurrency exchange.
    
    Args:
        exchange_id: ID of the cryptocurrency exchange (e.g., 'binance')
        days: Number of days of historical data to retrieve (default: 30)
        display: Whether to display the results
        save: Whether to save the data to a JSON file
        output: Optional custom filename for saved data
        
    Returns:
        List of data points with [timestamp, volume_btc] structure
    """
    try:
        # Validate days parameter
        if days <= 0:
            print_error("Number of days must be positive.")
            return []
            
        # Set up progress display
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            # Create task
            task = progress.add_task(f"[cyan]Fetching volume data for {exchange_id}...", total=1)
            
            # Fetch volume data from the exchange volume endpoint
            endpoint = f"exchanges/{exchange_id}/volume_chart"
            params = {'days': days}
            volume_data = api._make_request(endpoint, params)
            
            # Update progress
            progress.update(task, completed=1)
        
        if not volume_data or not isinstance(volume_data, list) or len(volume_data) == 0:
            print_error(f"No volume data found for exchange {exchange_id} over the last {days} days.")
            return []
            
        # Display results if requested
        if display:
            display_exchange_volume(volume_data, exchange_id, days)
            
        # Save data if requested
        if save:
            file_path = save_exchange_volume_data(volume_data, exchange_id, days, output)
            print_success(f"Exchange volume data saved to: {file_path}")
            
        return volume_data
        
    except Exception as e:
        print_error(f"Error retrieving exchange volume history: {str(e)}")
        return []

def display_exchange_volume(
    volume_data: List[List[float]],
    exchange_id: str,
    days: int
) -> None:
    """
    Display historical exchange volume data in a formatted table and chart.
    
    Args:
        volume_data: List of [timestamp, volume_btc] data points
        exchange_id: ID of the cryptocurrency exchange
        days: Number of days of historical data
    """
    if not volume_data or len(volume_data) == 0:
        print_warning("No volume data to display.")
        return
    
    # Create a table for volume data
    table = Table(
        title=f"📊 Historical Trading Volume for {exchange_id.capitalize()} (Last {days} Days)",
        box=ROUNDED
    )
    
    # Add columns
    table.add_column("Date", style="cyan")
    table.add_column("Volume (BTC)", justify="right")
    table.add_column("Change from Previous", justify="right")
    
    # Process data for display - limit to showing key data points to avoid overcrowding
    display_intervals = {
        7: 1,       # Show every day for 1 week
        14: 1,      # Show every day for 2 weeks
        30: 2,      # Show every 2 days for 1 month
        60: 4,      # Show every 4 days for 2 months
        90: 6,      # Show every 6 days for 3 months
        180: 10,    # Show every 10 days for 6 months
        365: 20,    # Show every 20 days for 1 year
        730: 40,    # Show every 40 days for 2 years
    }
    
    # Determine display interval
    interval = 1
    for max_days, step in sorted(display_intervals.items()):
        if days <= max_days:
            interval = step
            break
    else:
        interval = 30  # Default for very long periods
    
    # Sort data by timestamp (oldest to newest)
    sorted_data = sorted(volume_data, key=lambda x: x[0])
    
    # Get rows to display based on interval
    display_data = []
    for i in range(0, len(sorted_data), interval):
        display_data.append(sorted_data[i])
    
    # Always include the most recent day
    if sorted_data and display_data[-1] != sorted_data[-1]:
        display_data.append(sorted_data[-1])
    
    # Add rows to table
    prev_volume = None
    for data_point in display_data:
        timestamp = data_point[0]  # Timestamp in milliseconds
        volume = data_point[1]     # Volume in BTC
        
        # Convert timestamp to date string
        date_str = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d')
        
        # Format volume
        volume_str = f"₿ {volume:,.2f}"
        
        # Calculate and format change from previous
        if prev_volume is not None:
            change = volume - prev_volume
            change_percentage = (change / prev_volume) * 100 if prev_volume > 0 else 0
            
            if change > 0:
                change_str = f"[green]+{change:,.2f} BTC (+{change_percentage:.2f}%)[/green]"
            elif change < 0:
                change_str = f"[red]{change:,.2f} BTC ({change_percentage:.2f}%)[/red]"
            else:
                change_str = "No change"
        else:
            change_str = "N/A"
        
        # Add row to table
        table.add_row(
            date_str,
            volume_str,
            change_str
        )
        
        prev_volume = volume
    
    # Display the table
    console.print("\n")
    console.print(table)
    
    # Display volume statistics
    if volume_data:
        volumes = [point[1] for point in volume_data]
        avg_volume = sum(volumes) / len(volumes)
        max_volume = max(volumes)
        min_volume = min(volumes)
        median_volume = statistics.median(volumes)
        
        # Calculate volatility (standard deviation)
        if len(volumes) > 1:
            vol_std_dev = statistics.stdev(volumes)
            vol_std_dev_percentage = (vol_std_dev / avg_volume) * 100 if avg_volume > 0 else 0
        else:
            vol_std_dev = 0
            vol_std_dev_percentage = 0
        
        # Calculate overall trend
        if len(volumes) > 1:
            first_volume = volumes[0]
            last_volume = volumes[-1]
            overall_change = last_volume - first_volume
            overall_change_pct = (overall_change / first_volume) * 100 if first_volume > 0 else 0
        else:
            overall_change = 0
            overall_change_pct = 0
        
        # Display statistics
        console.print("\n[bold]Volume Statistics:[/bold]")
        console.print(f"Average Daily Volume: ₿ {avg_volume:,.2f}")
        console.print(f"Median Daily Volume: ₿ {median_volume:,.2f}")
        console.print(f"Highest Daily Volume: ₿ {max_volume:,.2f}")
        console.print(f"Lowest Daily Volume: ₿ {min_volume:,.2f}")
        console.print(f"Volume Volatility: ₿ {vol_std_dev:,.2f} ({vol_std_dev_percentage:.2f}% of average)")
        
        # Display trend
        console.print("\n[bold]Volume Trend:[/bold]")
        if overall_change > 0:
            console.print(f"Overall Change: [green]+{overall_change:,.2f} BTC (+{overall_change_pct:.2f}%)[/green]")
            console.print(f"Trend Direction: [green]Increasing[/green]")
        elif overall_change < 0:
            console.print(f"Overall Change: [red]{overall_change:,.2f} BTC ({overall_change_pct:.2f}%)[/red]")
            console.print(f"Trend Direction: [red]Decreasing[/red]")
        else:
            console.print(f"Overall Change: No change")
            console.print(f"Trend Direction: [yellow]Stable[/yellow]")
        
        # Calculate recent trend (last 7 days or the whole period if shorter)
        recent_period = min(7, len(volumes))
        if recent_period > 1:
            recent_volumes = volumes[-recent_period:]
            first_recent = recent_volumes[0]
            last_recent = recent_volumes[-1]
            recent_change = last_recent - first_recent
            recent_change_pct = (recent_change / first_recent) * 100 if first_recent > 0 else 0
            
            console.print(f"\n[bold]Recent Trend (Last {recent_period} Days):[/bold]")
            if recent_change > 0:
                console.print(f"Recent Change: [green]+{recent_change:,.2f} BTC (+{recent_change_pct:.2f}%)[/green]")
            elif recent_change < 0:
                console.print(f"Recent Change: [red]{recent_change:,.2f} BTC ({recent_change_pct:.2f}%)[/red]")
            else:
                console.print(f"Recent Change: No change")
    
    # Display ASCII chart of volume data
    try:
        # Create a simpler data structure for the chart function
        chart_data = []
        for point in sorted_data:
            timestamp = point[0]  # Unix timestamp in milliseconds
            volume = point[1]     # Volume in BTC
            
            # Create a data point in the format expected by display_ascii_chart
            # Format is [timestamp, open, high, low, close] but we just need timestamp and volume
            chart_data.append([timestamp, volume, volume, volume, volume])
        
        # Display the chart
        display_ascii_chart(chart_data, exchange_id, width=70, height=15)
    except Exception as e:
        # If visualization fails, show a simplified chart
        display_simple_volume_chart(sorted_data, exchange_id)
    
    # Display timestamp
    console.print(f"\n[dim]Data retrieved at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")

def display_simple_volume_chart(
    volume_data: List[List[float]],
    exchange_id: str,
    width: int = 60,
    height: int = 15
) -> None:
    """
    Display a simple ASCII chart of volume data.
    
    Args:
        volume_data: List of [timestamp, volume] data points
        exchange_id: ID of the cryptocurrency exchange
        width: Width of the chart in characters
        height: Height of the chart in characters
    """
    if not volume_data or len(volume_data) < 2:
        return
    
    # Extract timestamps and volumes
    timestamps = [point[0] for point in volume_data]
    volumes = [point[1] for point in volume_data]
    
    # Find min and max for scaling
    min_volume = min(volumes)
    max_volume = max(volumes)
    volume_range = max_volume - min_volume
    
    # Avoid division by zero
    if volume_range == 0:
        volume_range = 1
    
    # Create the chart
    chart = [f"Volume Chart for {exchange_id.capitalize()}"]
    chart.append(f"Range: ₿ {min_volume:,.2f} - ₿ {max_volume:,.2f}")
    chart.append("")
    
    # Create y-axis labels and grid
    grid = []
    y_labels = []
    
    for i in range(height):
        # Calculate volume at this height
        volume = max_volume - (i * volume_range / (height - 1))
        # Format the label
        label = f"₿ {volume:,.2f}".ljust(12)
        y_labels.append(label)
        
        # Create a grid row
        row = [' ' for _ in range(width)]
        grid.append(row)
    
    # Calculate x positions for each data point
    num_points = len(volumes)
    x_positions = []
    
    for i in range(num_points):
        # Calculate position along the width
        pos = int((i / (num_points - 1)) * (width - 1)) if num_points > 1 else 0
        x_positions.append(pos)
    
    # Calculate y positions for each data point
    y_positions = []
    
    for volume in volumes:
        # Scale the volume to chart height
        pos = int(((max_volume - volume) / volume_range) * (height - 1)) if volume_range > 0 else 0
        y_positions.append(pos)
    
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
                if 0 <= y < height and 0 <= x1 < width and grid[y][x1] == ' ':
                    grid[y][x1] = '│'
        elif y1 == y2:
            # Horizontal line
            start, end = min(x1, x2), max(x1, x2)
            for x in range(start + 1, end):
                if 0 <= y1 < height and 0 <= x < width and grid[y1][x] == ' ':
                    grid[y1][x] = '─'
        else:
            # Diagonal line
            dx = abs(x2 - x1)
            dy = abs(y2 - y1)
            sx = 1 if x1 < x2 else -1
            sy = 1 if y1 < y2 else -1
            err = dx - dy
            
            while (x1 != x2 or y1 != y2):
                if 0 <= y1 < height and 0 <= x1 < width and grid[y1][x1] == ' ':
                    # Choose the appropriate character for diagonal lines
                    grid[y1][x1] = '/' if (sx > 0 and sy < 0) or (sx < 0 and sy > 0) else '\\'
                
                e2 = 2 * err
                if e2 > -dy:
                    err -= dy
                    x1 += sx
                if e2 < dx:
                    err += dx
                    y1 += sy
    
    # Combine y-labels and grid to create the chart
    for i in range(height):
        line = y_labels[i] + ''.join(grid[i])
        chart.append(line)
    
    # Add x-axis
    chart.append('-' * (width + 12))
    
    # Add x-axis labels (dates) - just show a few to avoid overcrowding
    label_positions = [0, num_points // 4, num_points // 2, 3 * num_points // 4, num_points - 1]
    label_positions = [p for p in label_positions if p < num_points]  # Ensure all positions are valid
    
    date_labels = []
    for i in label_positions:
        timestamp = timestamps[i]
        date_str = datetime.fromtimestamp(timestamp / 1000).strftime('%m/%d')
        pos = x_positions[i] + 12  # Adjust for y-axis label width
        date_labels.append((pos, date_str))
    
    # Create x-axis label line with dates positioned correctly
    x_label_line = ' ' * (width + 12)
    for pos, label in date_labels:
        if 0 <= pos < len(x_label_line):
            # Place label centered at position
            start_idx = max(0, pos - len(label) // 2)
            end_idx = min(len(x_label_line), start_idx + len(label))
            
            x_label_line = (
                x_label_line[:start_idx] + 
                label[:end_idx-start_idx] + 
                x_label_line[end_idx:]
            )
    
    chart.append(x_label_line)
    
    # Print the chart
    console.print('\n'.join(chart))

def save_exchange_volume_data(
    volume_data: List[List[float]],
    exchange_id: str,
    days: int,
    filename: Optional[str] = None
) -> str:
    """
    Save exchange volume history to a JSON file.
    
    Args:
        volume_data: List of data points with [timestamp, volume_btc] structure
        exchange_id: ID of the cryptocurrency exchange
        days: Number of days of historical data
        filename: Optional custom filename for saved data
        
    Returns:
        Path to the saved file
    """
    if not volume_data:
        print_error("No data to save.")
        return ""
    
    # Generate default filename if not provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{exchange_id}_volume_history_{days}d_{timestamp}.json"
    
    # Ensure filename has .json extension
    if not filename.endswith('.json'):
        filename += '.json'
    
    try:
        # Process data for a more readable format
        processed_data = []
        
        for data_point in volume_data:
            unix_time = data_point[0]  # Timestamp in milliseconds
            volume = data_point[1]     # Volume in BTC
            
            # Convert to readable date for reference
            date_str = datetime.fromtimestamp(unix_time / 1000).strftime('%Y-%m-%d %H:%M:%S')
            
            # Create record with both unix time and human-readable date
            record = {
                "unix_timestamp_ms": unix_time,
                "date": date_str,
                "volume_btc": volume
            }
            
            processed_data.append(record)
        
        # Create data object with metadata
        data_object = {
            "exchange_id": exchange_id,
            "days": days,
            "data_points": len(volume_data),
            "generated_at": datetime.now().isoformat(),
            "volume_data": processed_data
        }
        
        # Calculate some statistics for the metadata
        volumes = [point[1] for point in volume_data]
        if volumes:
            data_object["statistics"] = {
                "average_volume": sum(volumes) / len(volumes),
                "max_volume": max(volumes),
                "min_volume": min(volumes),
                "median_volume": statistics.median(volumes),
                "total_volume": sum(volumes)
            }
            
            # Calculate trend data if we have more than one data point
            if len(volumes) > 1:
                first_volume = volumes[0]
                last_volume = volumes[-1]
                change = last_volume - first_volume
                change_pct = (change / first_volume) * 100 if first_volume > 0 else 0
                
                data_object["trend"] = {
                    "start_volume": first_volume,
                    "end_volume": last_volume,
                    "absolute_change": change,
                    "percentage_change": change_pct
                }
        
        # Write to file
        with open(filename, 'w') as f:
            json.dump(data_object, f, indent=4)
            
        return os.path.abspath(filename)
    
    except Exception as e:
        print_error(f"Failed to save exchange volume data: {str(e)}")
        return ""

def analyze_volume_patterns(
    volume_data: List[List[float]],
    exchange_id: str
) -> None:
    """
    Perform advanced analysis of volume patterns for an exchange.
    
    Args:
        volume_data: List of data points with [timestamp, volume_btc] structure
        exchange_id: ID of the cryptocurrency exchange
    """
    if not volume_data or len(volume_data) < 7:  # Need at least a week of data
        print_warning("Not enough data for pattern analysis. Minimum 7 data points required.")
        return
    
    # Sort data by timestamp (oldest to newest)
    sorted_data = sorted(volume_data, key=lambda x: x[0])
    
    # Extract timestamps and volumes
    timestamps = [point[0] for point in sorted_data]
    volumes = [point[1] for point in sorted_data]
    
    # Convert timestamps to datetime objects
    dates = [datetime.fromtimestamp(ts / 1000) for ts in timestamps]
    
    console.print("\n[bold cyan]📊 Volume Pattern Analysis[/bold cyan]\n")
    
    # Calculate daily change percentages
    daily_changes = []
    for i in range(1, len(volumes)):
        if volumes[i-1] > 0:
            change = ((volumes[i] - volumes[i-1]) / volumes[i-1]) * 100
            daily_changes.append(change)
    
    if daily_changes:
        # Calculate volatility metrics
        mean_change = sum(daily_changes) / len(daily_changes)
        abs_changes = [abs(change) for change in daily_changes]
        mean_abs_change = sum(abs_changes) / len(abs_changes)
        
        console.print(f"[bold]Daily Change Statistics:[/bold]")
        console.print(f"Average Daily Change: {mean_change:.2f}%")
        console.print(f"Average Absolute Change: {mean_abs_change:.2f}%")
        
        # Identify significant volume days (outliers)
        mean_volume = sum(volumes) / len(volumes)
        std_dev_volume = statistics.stdev(volumes) if len(volumes) > 1 else 0
        
        significant_days = []
        for i, volume in enumerate(volumes):
            if abs(volume - mean_volume) > 2 * std_dev_volume:  # More than 2 standard deviations
                significant_days.append((dates[i], volume, (volume - mean_volume) / mean_volume * 100))
        
        if significant_days:
            console.print(f"\n[bold]Significant Volume Days:[/bold]")
            for date, volume, percent_diff in significant_days:
                date_str = date.strftime('%Y-%m-%d')
                if percent_diff > 0:
                    console.print(f"{date_str}: ₿ {volume:,.2f} ([green]+{percent_diff:.2f}%[/green] above average)")
                else:
                    console.print(f"{date_str}: ₿ {volume:,.2f} ([red]{percent_diff:.2f}%[/red] below average)")
        else:
            console.print(f"\n[bold]Significant Volume Days:[/bold] None detected")
    
    # Detect weekly patterns
    if len(dates) >= 14:  # Need at least 2 weeks of data
        # Group volumes by day of week
        day_of_week_volumes = {i: [] for i in range(7)}  # 0 = Monday, 6 = Sunday
        
        for i, date in enumerate(dates):
            day_of_week_volumes[date.weekday()].append(volumes[i])
        
        # Calculate average volume by day of week
        day_of_week_averages = {}
        for day, vols in day_of_week_volumes.items():
            if vols:
                day_of_week_averages[day] = sum(vols) / len(vols)
        
        if day_of_week_averages:
            # Find day of week with highest and lowest average volume
            highest_day = max(day_of_week_averages.items(), key=lambda x: x[1])
            lowest_day = min(day_of_week_averages.items(), key=lambda x: x[1])
            
            # Day names
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            
            console.print(f"\n[bold]Weekly Patterns:[/bold]")
            console.print(f"Highest Volume Day: {day_names[highest_day[0]]} (₿ {highest_day[1]:,.2f})")
            console.print(f"Lowest Volume Day: {day_names[lowest_day[0]]} (₿ {lowest_day[1]:,.2f})")
            
            # Calculate weekend vs weekday volume
            weekday_vols = []
            for day in range(0, 5):  # Monday to Friday
                weekday_vols.extend(day_of_week_volumes[day])
                
            weekend_vols = []
            for day in range(5, 7):  # Saturday and Sunday
                weekend_vols.extend(day_of_week_volumes[day])
            
            if weekday_vols and weekend_vols:
                avg_weekday = sum(weekday_vols) / len(weekday_vols)
                avg_weekend = sum(weekend_vols) / len(weekend_vols)
                
                diff_pct = ((avg_weekend - avg_weekday) / avg_weekday) * 100 if avg_weekday > 0 else 0
                
                console.print(f"Average Weekday Volume: ₿ {avg_weekday:,.2f}")
                console.print(f"Average Weekend Volume: ₿ {avg_weekend:,.2f}")
                
                if diff_pct > 0:
                    console.print(f"Weekend vs Weekday: [green]+{diff_pct:.2f}%[/green] higher on weekends")
                else:
                    console.print(f"Weekend vs Weekday: [red]{diff_pct:.2f}%[/red] lower on weekends")
    
    # Identify trends and patterns
    if len(volumes) >= 7:
        # Calculate 7-day moving average
        moving_averages = []
        for i in range(7, len(volumes) + 1):
            window = volumes[i-7:i]
            moving_averages.append(sum(window) / 7)
        
        if moving_averages:
            # Determine if volume is trending up, down, or stable
            first_ma = moving_averages[0]
            last_ma = moving_averages[-1]
            ma_change = ((last_ma - first_ma) / first_ma) * 100 if first_ma > 0 else 0
            
            console.print(f"\n[bold]Moving Average Trend:[/bold]")
            if ma_change > 10:
                console.print(f"7-Day MA Change: [green]+{ma_change:.2f}%[/green] (Strongly Increasing)")
            elif ma_change > 3:
                console.print(f"7-Day MA Change: [green]+{ma_change:.2f}%[/green] (Moderately Increasing)")
            elif ma_change > 0:
                console.print(f"7-Day MA Change: [green]+{ma_change:.2f}%[/green] (Slightly Increasing)")
            elif ma_change > -3:
                console.print(f"7-Day MA Change: [yellow]{ma_change:.2f}%[/yellow] (Relatively Stable)")
            elif ma_change > -10:
                console.print(f"7-Day MA Change: [red]{ma_change:.2f}%[/red] (Moderately Decreasing)")
            else:
                console.print(f"7-Day MA Change: [red]{ma_change:.2f}%[/red] (Strongly Decreasing)")
            
            # Check for recent volume spikes or drops
            recent_period = min(7, len(volumes))
            recent_volumes = volumes[-recent_period:]
            recent_avg = sum(recent_volumes) / len(recent_volumes)
            
            # Compare to the previous period
            if len(volumes) > recent_period * 2:
                prev_period = volumes[-(recent_period*2):-recent_period]
                prev_avg = sum(prev_period) / len(prev_period)
                
                recent_change = ((recent_avg - prev_avg) / prev_avg) * 100 if prev_avg > 0 else 0
                
                console.print(f"\n[bold]Recent Volume Change:[/bold]")
                if recent_change > 20:
                    console.print(f"Last {recent_period} days vs previous {recent_period}: [green]+{recent_change:.2f}%[/green] (Significant Increase)")
                elif recent_change > 5:
                    console.print(f"Last {recent_period} days vs previous {recent_period}: [green]+{recent_change:.2f}%[/green] (Moderate Increase)")
                elif recent_change > -5:
                    console.print(f"Last {recent_period} days vs previous {recent_period}: [yellow]{recent_change:.2f}%[/yellow] (Stable)")
                elif recent_change > -20:
                    console.print(f"Last {recent_period} days vs previous {recent_period}: [red]{recent_change:.2f}%[/red] (Moderate Decrease)")
                else:
                    console.print(f"Last {recent_period} days vs previous {recent_period}: [red]{recent_change:.2f}%[/red] (Significant Decrease)")
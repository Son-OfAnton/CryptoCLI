"""
Module for retrieving and displaying historical circulating supply data for cryptocurrencies.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import time
import json
import os
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn

from app.api import api
from app.utils.formatting import (
    console,
    print_error,
    print_warning,
    print_success,
    format_large_number,
)

def get_supply_history(
    coin_id: str,
    days: int = 30,
    display: bool = True,
    save: bool = False,
    output: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get historical circulating supply data for a cryptocurrency over a specified number of days.
    
    Args:
        coin_id: ID of the cryptocurrency (e.g., 'bitcoin')
        days: Number of days of historical data to retrieve
        display: Whether to display the data in the console
        save: Whether to save the data to a JSON file
        output: Optional filename to save data to
        
    Returns:
        List of dictionaries containing supply data for each day
    """
    try:
        # Validate days parameter
        if days <= 0:
            print_error("Number of days must be positive.")
            return []
            
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            # Create progress tasks
            fetch_task = progress.add_task("[cyan]Fetching supply data...", total=2)
            
            # Step 1: Get circulating supply chart data using the dedicated endpoint
            supply_chart_endpoint = f"coins/{coin_id}/circulating_supply_chart"
            params = {"days": days}
            supply_chart_data = api._make_request(supply_chart_endpoint, params)
            progress.update(fetch_task, advance=1)
            
            # Step 2: Get current coin data for context and additional information
            coin_data = api.get_coin_data(coin_id)
            progress.update(fetch_task, advance=1)
            
        if not supply_chart_data:
            print_error(f"Failed to retrieve supply chart data for {coin_id}.")
            return []
            
        # Extract supply data from the response
        supply_points = supply_chart_data.get('circulating_supplies', [])
        
        if not supply_points or len(supply_points) == 0:
            print_warning(f"No circulating supply data available for {coin_id}.")
            return []
            
        # Get current supply from coin data for context
        current_supply = coin_data.get('market_data', {}).get('circulating_supply')
        if current_supply is None:
            print_warning("Could not get current supply data from coin information.")
            # Use the last data point from the chart as current supply
            if supply_points:
                current_supply = supply_points[-1][1]
            else:
                current_supply = 0
        
        # Transform data into a more usable format
        supply_data = []
        for point in supply_points:
            timestamp = point[0]  # Timestamp in milliseconds
            supply = point[1]     # Circulating supply value
            
            # Create data point
            data_point = {
                "timestamp": timestamp,
                "date": datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d'),
                "circulating_supply": supply
            }
            
            # Add market cap if available in coin data
            price_usd = coin_data.get('market_data', {}).get('current_price', {}).get('usd')
            if price_usd is not None:
                # Estimate historical market cap based on supply and current price
                # This is just an approximation as actual historical prices varied
                estimated_market_cap = supply * price_usd
                data_point["estimated_market_cap"] = estimated_market_cap
            
            supply_data.append(data_point)
        
        # Sort by timestamp (oldest to newest)
        supply_data.sort(key=lambda x: x['timestamp'])
        
        # Display data if requested
        if display:
            display_supply_history(supply_data, coin_id, days, current_supply)
        
        # Save data if requested
        if save:
            file_path = save_supply_history(supply_data, coin_id, days, current_supply, output)
            print_success(f"Supply history data saved to: {file_path}")
            
        return supply_data
    
    except Exception as e:
        print_error(f"Error retrieving supply history: {str(e)}")
        return []

def display_supply_history(
    supply_data: List[Dict[str, Any]],
    coin_id: str,
    days: int,
    current_supply: float
):
    """
    Display historical circulating supply data in a formatted table.
    
    Args:
        supply_data: List of dictionaries containing supply data for each day
        coin_id: ID of the cryptocurrency
        days: Number of days of historical data
        current_supply: Current circulating supply
    """
    if not supply_data:
        print_warning("No supply data to display.")
        return
    
    # Create table for displaying supply data
    table = Table(
        title=f"Historical Circulating Supply for {coin_id.capitalize()} (Last {days} Days)",
        box=box.ROUNDED
    )
    
    # Add columns
    table.add_column("Date", style="cyan")
    table.add_column("Circulating Supply", justify="right")
    table.add_column("Change from Previous", justify="right")
    table.add_column("% of Current Supply", justify="right")
    table.add_column("Estimated Market Cap", justify="right")
    
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
    
    # Get rows to display based on interval
    display_data = []
    for i in range(0, len(supply_data), interval):
        display_data.append(supply_data[i])
    
    # Always include the most recent day
    if supply_data and display_data[-1] != supply_data[-1]:
        display_data.append(supply_data[-1])
    
    # Add rows to table
    prev_supply = None
    for data_point in display_data:
        date = data_point['date']
        supply = data_point['circulating_supply']
        
        # Format supply
        formatted_supply = format_large_number(supply)
        
        # Calculate and format change from previous
        if prev_supply is not None:
            change = supply - prev_supply
            change_percentage = (change / prev_supply) * 100 if prev_supply > 0 else 0
            
            if change > 0:
                formatted_change = f"[green]+{format_large_number(change)} (+{change_percentage:.2f}%)[/green]"
            elif change < 0:
                formatted_change = f"[red]{format_large_number(change)} ({change_percentage:.2f}%)[/red]"
            else:
                formatted_change = "No change"
        else:
            formatted_change = "N/A"
        
        # Calculate percentage of current supply
        if current_supply > 0:
            supply_percentage = (supply / current_supply) * 100
            formatted_percentage = f"{supply_percentage:.2f}%"
        else:
            formatted_percentage = "N/A"
        
        # Format market cap if available
        if "estimated_market_cap" in data_point:
            formatted_market_cap = f"${format_large_number(data_point['estimated_market_cap'])}"
        else:
            formatted_market_cap = "N/A"
        
        # Add row to table
        table.add_row(
            date,
            formatted_supply,
            formatted_change,
            formatted_percentage,
            formatted_market_cap
        )
        
        prev_supply = supply
    
    # Display the table
    console.print("\n")
    console.print(table)
    
    # Display summary information
    if supply_data:
        first_supply = supply_data[0]['circulating_supply']
        last_supply = supply_data[-1]['circulating_supply']
        supply_change = last_supply - first_supply
        supply_change_pct = (supply_change / first_supply) * 100 if first_supply > 0 else 0
        
        console.print(f"\n[bold]Supply Summary:[/bold]")
        console.print(f"Starting Supply ({supply_data[0]['date']}): {format_large_number(first_supply)}")
        console.print(f"Current Supply ({supply_data[-1]['date']}): {format_large_number(last_supply)}")
        
        if supply_change > 0:
            console.print(f"Total Change: [green]+{format_large_number(supply_change)} (+{supply_change_pct:.2f}%)[/green]")
        elif supply_change < 0:
            console.print(f"Total Change: [red]{format_large_number(supply_change)} ({supply_change_pct:.2f}%)[/red]")
        else:
            console.print("Total Change: No change")
        
        # Calculate average daily change
        if len(supply_data) > 1:
            avg_daily_change = supply_change / (len(supply_data) - 1)
            avg_daily_pct = (avg_daily_change / first_supply) * 100 if first_supply > 0 else 0
            
            if avg_daily_change > 0:
                console.print(f"Average Daily Change: [green]+{format_large_number(avg_daily_change)} (+{avg_daily_pct:.4f}%/day)[/green]")
            elif avg_daily_change < 0:
                console.print(f"Average Daily Change: [red]{format_large_number(avg_daily_change)} ({avg_daily_pct:.4f}%/day)[/red]")
            else:
                console.print("Average Daily Change: No change")
            
    # Display timestamp
    console.print(f"\n[dim]Data retrieved at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")

def analyze_supply_trends(supply_data: List[Dict[str, Any]], coin_id: str):
    """
    Analyze trends in the circulating supply data.
    
    Args:
        supply_data: List of dictionaries containing supply data for each day
        coin_id: ID of the cryptocurrency
    """
    if not supply_data or len(supply_data) < 2:
        print_warning("Not enough data to analyze trends.")
        return
    
    console.print("\n[bold cyan]📊 Circulating Supply Trend Analysis[/bold cyan]")
    
    # Calculate daily changes
    daily_changes = []
    prev_supply = None
    for data_point in supply_data:
        supply = data_point['circulating_supply']
        if prev_supply is not None:
            change = supply - prev_supply
            change_pct = (change / prev_supply) * 100 if prev_supply > 0 else 0
            daily_changes.append(change_pct)
        prev_supply = supply
    
    # Calculate statistics
    avg_daily_change_pct = sum(daily_changes) / len(daily_changes) if daily_changes else 0
    max_daily_increase = max(daily_changes) if daily_changes else 0
    max_daily_decrease = min(daily_changes) if daily_changes else 0
    
    # Find days with significant changes
    significant_changes = []
    for i, change in enumerate(daily_changes):
        if abs(change) > 1.0:  # More than 1% change in a day is significant
            date = supply_data[i+1]['date']  # +1 because changes start from the second data point
            significant_changes.append((date, change))
    
    # Sort significant changes by magnitude
    significant_changes.sort(key=lambda x: abs(x[1]), reverse=True)
    
    # Display trend information
    console.print(f"\n[bold]Supply Change Trend:[/bold]")
    
    if avg_daily_change_pct > 0.01:
        console.print(f"Average Daily Increase: [green]+{avg_daily_change_pct:.4f}%[/green]")
        console.print(f"Emission Status: [green]Inflationary[/green]")
        console.print(f"The circulating supply of {coin_id} has been [green]increasing[/green] on average during this period.")
    elif avg_daily_change_pct < -0.01:
        console.print(f"Average Daily Decrease: [red]{avg_daily_change_pct:.4f}%[/red]")
        console.print(f"Emission Status: [blue]Deflationary[/blue]")
        console.print(f"The circulating supply of {coin_id} has been [blue]decreasing[/blue] on average during this period.")
    else:
        console.print(f"Average Daily Change: {avg_daily_change_pct:.4f}%")
        console.print(f"Emission Status: [yellow]Stable[/yellow]")
        console.print(f"The circulating supply of {coin_id} has been [yellow]relatively stable[/yellow] during this period.")
    
    console.print(f"\n[bold]Notable Statistics:[/bold]")
    console.print(f"Largest Daily Increase: [green]+{max_daily_increase:.4f}%[/green]")
    console.print(f"Largest Daily Decrease: [red]{max_daily_decrease:.4f}%[/red]")
    
    if significant_changes:
        console.print(f"\n[bold]Significant Supply Changes:[/bold]")
        for date, change in significant_changes[:5]:  # Show top 5 most significant changes
            if change > 0:
                console.print(f"{date}: [green]+{change:.4f}%[/green]")
            else:
                console.print(f"{date}: [red]{change:.4f}%[/red]")
    else:
        console.print("\n[bold]Significant Supply Changes:[/bold] None detected")
    
    # Estimate annual inflation/deflation rate
    annual_rate = avg_daily_change_pct * 365
    console.print(f"\n[bold]Estimated Annual Rate:[/bold] ", end="")
    if annual_rate > 1:
        console.print(f"[green]+{annual_rate:.2f}%[/green] (inflationary)")
    elif annual_rate < -1:
        console.print(f"[blue]{annual_rate:.2f}%[/blue] (deflationary)")
    else:
        console.print(f"[yellow]{annual_rate:.2f}%[/yellow] (stable)")

def save_supply_history(
    supply_data: List[Dict[str, Any]],
    coin_id: str,
    days: int,
    current_supply: float,
    filename: Optional[str] = None
) -> str:
    """
    Save supply history data to a JSON file.
    
    Args:
        supply_data: List of dictionaries containing supply data for each day
        coin_id: ID of the cryptocurrency
        days: Number of days of historical data
        current_supply: Current circulating supply
        filename: Optional filename to save data to
        
    Returns:
        Path to the saved file
    """
    if not supply_data:
        print_error("No data to save.")
        return ""
    
    # Generate default filename if not provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{coin_id}_supply_history_{days}d_{timestamp}.json"
    
    # Ensure filename has .json extension
    if not filename.endswith('.json'):
        filename += '.json'
    
    try:
        # Calculate some summary statistics for the metadata
        first_supply = supply_data[0]['circulating_supply']
        last_supply = supply_data[-1]['circulating_supply']
        total_change = last_supply - first_supply
        percent_change = (total_change / first_supply) * 100 if first_supply > 0 else 0
        
        # Create data object with metadata
        data_object = {
            "coin_id": coin_id,
            "days": days,
            "current_supply": current_supply,
            "data_points": len(supply_data),
            "first_date": supply_data[0]['date'],
            "last_date": supply_data[-1]['date'],
            "starting_supply": first_supply,
            "ending_supply": last_supply,
            "total_change": total_change,
            "percent_change": percent_change,
            "generated_at": int(time.time()),
            "supply_data": supply_data
        }
        
        # Write to file
        with open(filename, 'w') as f:
            json.dump(data_object, f, indent=4)
            
        return os.path.abspath(filename)
    
    except Exception as e:
        print_error(f"Failed to save supply history: {str(e)}")
        return ""
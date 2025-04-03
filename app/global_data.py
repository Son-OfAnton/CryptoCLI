"""
Functionality for retrieving and displaying global cryptocurrency market data.
"""
from app.api import api
from app.utils.formatting import console, print_error, format_currency, format_large_number
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
import json
import os
from datetime import datetime

def get_global_data(display=True, save=False, output=None):
    """
    Get and optionally display global cryptocurrency market data.
    
    Args:
        display (bool): Whether to display the data in the console
        save (bool): Whether to save the data to a file
        output (str, optional): Filename to save data to (if save is True)
        
    Returns:
        dict: Global cryptocurrency market data or None if an error occurs
    """
    try:
        # Get global data from API
        global_data = api.get_global_data()
        
        # Check if we have a valid response with data
        if not global_data or 'data' not in global_data:
            print_error("No global market data found.")
            return None
            
        # Extract just the data part
        data = global_data['data']
        
        # Display data if requested
        if display:
            display_global_data(data)
            
        # Save to file if requested
        if save:
            save_global_data(data, output)
            
        return data
        
    except Exception as e:
        print_error(f"Failed to retrieve global market data: {str(e)}")
        return None

def display_global_data(data):
    """
    Display global cryptocurrency market data in a well-formatted way.
    
    Args:
        data (dict): Global market data from the API
    """
    # Create a panel for overall market data
    market_panel = create_market_overview_panel(data)
    console.print(market_panel)
    
    # Create a table for market cap dominance
    dominance_table = create_dominance_table(data)
    console.print(dominance_table)
    
    # Display active cryptocurrencies and markets
    console.print(create_stats_panel(data))

def create_market_overview_panel(data):
    """Create a panel showing overall market data."""
    content = Text()
    
    # Market cap data
    mkt_cap_usd = data.get('total_market_cap', {}).get('usd', 0)
    content.append("Total Market Cap: ")
    content.append(f"{format_currency(mkt_cap_usd, 'usd')}", style="bold green")
    content.append(f" ({format_large_number(mkt_cap_usd)})\n")

    # 24h volume data
    volume_usd = data.get('total_volume', {}).get('usd', 0)
    content.append("24h Trading Volume: ")
    content.append(f"{format_currency(volume_usd, 'usd')}", style="bold blue")
    content.append(f" ({format_large_number(volume_usd)})\n")
    
    # Market cap to volume ratio
    if volume_usd > 0:
        mcap_to_vol_ratio = mkt_cap_usd / volume_usd
        content.append("Market Cap / Volume Ratio: ")
        content.append(f"{mcap_to_vol_ratio:.2f}\n", style="bold")
    
    # BTC dominance
    btc_dom = data.get('market_cap_percentage', {}).get('btc', 0)
    content.append("Bitcoin Dominance: ")
    content.append(f"{btc_dom:.2f}%\n", style="bold yellow")
    
    # ETH dominance
    eth_dom = data.get('market_cap_percentage', {}).get('eth', 0)
    content.append("Ethereum Dominance: ")
    content.append(f"{eth_dom:.2f}%\n", style="bold magenta")
    
    # Market cap change
    mkt_cap_change = data.get('market_cap_change_percentage_24h_usd', 0)
    content.append("24h Market Cap Change: ")
    if mkt_cap_change >= 0:
        content.append(f"+{mkt_cap_change:.2f}%\n", style="green")
    else:
        content.append(f"{mkt_cap_change:.2f}%\n", style="red")
        
    # Last updated
    last_updated = data.get('updated_at', 0)
    last_updated_str = datetime.fromtimestamp(last_updated).strftime('%Y-%m-%d %H:%M:%S UTC')
    content.append(f"\nLast Updated: {last_updated_str}", style="dim")
    
    return Panel(
        content,
        title="Global Cryptocurrency Market",
        border_style="green"
    )

def create_dominance_table(data):
    """Create a table showing market cap dominance by cryptocurrency."""
    table = Table(title="Market Cap Dominance by Coin")
    
    table.add_column("Rank", style="cyan", justify="right")
    table.add_column("Coin", style="yellow")
    table.add_column("Dominance (%)", style="green", justify="right")
    
    # Get market cap percentage data and sort by percentage
    dominance_data = data.get('market_cap_percentage', {})
    sorted_dominance = sorted(dominance_data.items(), key=lambda x: x[1], reverse=True)
    
    # Add rows for each coin
    for i, (coin, percentage) in enumerate(sorted_dominance, 1):
        table.add_row(
            str(i),
            coin.upper(),
            f"{percentage:.2f}%"
        )
    
    return table

def create_stats_panel(data):
    """Create a panel with additional market statistics."""
    content = Text()
    
    # Active cryptocurrencies
    content.append("Active Cryptocurrencies: ")
    content.append(f"{data.get('active_cryptocurrencies', 0):,}\n", style="bold")
    
    # Active exchanges
    content.append("Active Exchanges: ")
    content.append(f"{data.get('active_exchanges', 0):,}\n", style="bold")
    
    # Active markets
    content.append("Active Market Pairs: ")
    content.append(f"{data.get('active_market_pairs', 0):,}\n", style="bold")
    
    # ICO stats if available
    if 'ico_data' in data:
        ico_stats = data['ico_data']
        content.append("\nICO Statistics:\n", style="underline")
        content.append(f"Ongoing ICOs: {ico_stats.get('ongoing_icos', 0)}\n")
        content.append(f"Upcoming ICOs: {ico_stats.get('upcoming_icos', 0)}\n")
        content.append(f"Ended ICOs: {ico_stats.get('ended_icos', 0)}\n")
    
    return Panel(
        content,
        title="Market Statistics",
        border_style="blue"
    )

def save_global_data(data, filename=None):
    """
    Save global market data to a JSON file.
    
    Args:
        data (dict): Global market data from the API
        filename (str, optional): Filename to save data to
    """
    if filename is None:
        # Generate default filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"global_crypto_data_{timestamp}.json"
        
    try:
        # Format timestamp for readability in the saved file
        if 'updated_at' in data:
            updated_time = datetime.fromtimestamp(data['updated_at']).strftime('%Y-%m-%d %H:%M:%S UTC')
            data['updated_at_formatted'] = updated_time
        
        # Write to file with nice formatting
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
            
        console.print(f"[green]Global market data saved to[/green] {filename}")
        
    except Exception as e:
        print_error(f"Failed to save global market data: {str(e)}")
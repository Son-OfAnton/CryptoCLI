"""
Functionality for retrieving and displaying global DeFi market data from CoinGecko.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import os

from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from app.api import api
from .utils.formatting import (
    console, 
    print_error, 
    format_currency, 
    format_large_number,
    format_percentage
)

def get_defi_data(display=True, save=False, output=None, top_tokens=10):
    """
    Get and optionally display global DeFi market data.
    
    Args:
        display (bool): Whether to display the data in the console
        save (bool): Whether to save the data to a file
        output (str, optional): Filename to save data to (if save is True)
        top_tokens (int): Number of top DeFi tokens to display (1-100)
        
    Returns:
        dict: Global DeFi market data or None if an error occurs
    """
    try:
        # Get global DeFi data from API
        defi_data = api.get_global_defi_data()
        
        # Check if we have a valid response with data
        if not defi_data or 'data' not in defi_data:
            print_error("Failed to get global DeFi data from CoinGecko API.")
            return None
        
        data = defi_data['data']
        
        # Display the data if requested
        if display:
            display_defi_data(data, top_tokens)
        
        # Save the data if requested
        if save:
            file_path = save_defi_data(data, output)
            console.print(f"\n[green]DeFi data saved to:[/green] {file_path}")
        
        return data
    
    except Exception as e:
        print_error(f"Error retrieving global DeFi data: {str(e)}")
        return None

def display_defi_data(data: Dict[str, Any], top_tokens: int = 10):
    """
    Display global DeFi market data in a formatted way.
    
    Args:
        data (dict): Global DeFi market data
        top_tokens (int): Number of top DeFi tokens to display
    """
    # Limit top_tokens to range 1-100
    top_tokens = max(1, min(100, top_tokens))
    
    # Create market overview panel
    market_text = Text()
    market_text.append("\n🔹 [bold]DeFi Market Cap:[/bold] ")
    market_text.append(f"{format_currency(data['defi_market_cap'], 'USD')}\n")
    
    market_text.append("🔹 [bold]Ethereum Market Cap:[/bold] ")
    market_text.append(f"{format_currency(data['eth_market_cap'], 'USD')}\n")
    
    market_text.append("🔹 [bold]DeFi to Ethereum Ratio:[/bold] ")
    market_text.append(f"{format_percentage(data['defi_to_eth_ratio'])}\n")
    
    market_text.append("🔹 [bold]Trading Volume 24h:[/bold] ")
    market_text.append(f"{format_currency(data['trading_volume_24h'], 'USD')}\n")
    
    market_text.append("🔹 [bold]DeFi Dominance:[/bold] ")
    market_text.append(f"{format_percentage(data['defi_dominance'])}\n")
    
    market_text.append("🔹 [bold]Top DeFi Tokens by Market Cap:[/bold] ")
    market_text.append(f"{top_tokens} out of {data.get('top_coins_count', 100)}\n")
    
    # Create panel for market overview
    market_panel = Panel(
        market_text,
        title="[bold cyan]Global DeFi Market Overview[/bold cyan]",
        border_style="cyan"
    )
    console.print(market_panel)
    
    # Display top tokens in a table if they exist
    if 'top_coins_defi' in data and data['top_coins_defi']:
        display_top_tokens(data['top_coins_defi'][:top_tokens])

def display_top_tokens(tokens: List[Dict[str, Any]]):
    """
    Display top DeFi tokens in a table.
    
    Args:
        tokens (list): List of token data
    """
    table = Table(title="Top DeFi Tokens")
    
    # Define table columns
    table.add_column("Rank", style="dim", justify="right")
    table.add_column("Name", style="cyan")
    table.add_column("Symbol", style="blue")
    table.add_column("Market Cap", justify="right", style="green")
    table.add_column("Price", justify="right")
    table.add_column("Volume 24h", justify="right")
    table.add_column("Price Change 24h", justify="right")
    
    # Add rows to the table
    for i, token in enumerate(tokens, 1):
        name = token.get('name', 'Unknown')
        symbol = token.get('symbol', '?').upper()
        market_cap = format_currency(token.get('market_cap', 0), 'USD')
        price = format_currency(token.get('price', 0), 'USD')
        volume = format_currency(token.get('volume', 0), 'USD')
        
        price_change = token.get('price_change_24h', 0)
        if price_change > 0:
            price_change_str = f"[green]+{format_percentage(price_change)}[/green]"
        elif price_change < 0:
            price_change_str = f"[red]{format_percentage(price_change)}[/red]"
        else:
            price_change_str = f"{format_percentage(price_change)}"
        
        table.add_row(
            str(i),
            name,
            symbol,
            market_cap,
            price,
            volume,
            price_change_str
        )
    
    console.print("\n")
    console.print(table)

def save_defi_data(data: Dict[str, Any], filename: Optional[str] = None) -> str:
    """
    Save global DeFi market data to a JSON file.
    
    Args:
        data (dict): Global DeFi market data
        filename (str, optional): Filename to save data to
        
    Returns:
        str: Path to the saved file
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"defi_market_data_{timestamp}.json"
    
    # Ensure the filename has a .json extension
    if not filename.endswith('.json'):
        filename += '.json'
    
    # Write data to file
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    
    return os.path.abspath(filename)
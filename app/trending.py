"""
Functionality for retrieving and displaying trending coins from CoinGecko.
"""
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import os

from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.console import Console

from app.api import api
from app.utils.formatting import (
    console, 
    print_error, 
    print_warning,
    format_currency, 
    format_large_number,
    format_percentage
)

def get_trending_coins(display=True, save=False, output=None):
    """
    Get and display trending cryptocurrencies in the last 24 hours.
    
    Args:
        display (bool): Whether to display the data in the console
        save (bool): Whether to save the data to a file
        output (str, optional): Filename to save data to (if save is True)
        
    Returns:
        dict: Trending coins data or None if an error occurs
    """
    try:
        # Get trending coins from API
        trending_data = api.get_trending_coins()
        
        # Check if we have a valid response with coins data
        if not trending_data or 'coins' not in trending_data:
            print_error("Failed to get trending coins data from CoinGecko API.")
            return None
        
        # Display the data if requested
        if display:
            display_trending_coins(trending_data)
        
        # Save the data if requested
        if save:
            file_path = save_trending_data(trending_data, output)
            console.print(f"\n[green]Trending coins data saved to:[/green] {file_path}")
        
        return trending_data
    
    except Exception as e:
        print_error(f"Error retrieving trending coins: {str(e)}")
        return None

def display_trending_coins(trending_data: Dict[str, Any]):
    """
    Display trending cryptocurrencies in a formatted table.
    
    Args:
        trending_data (dict): Trending coins data from the API
    """
    # Check if we have coins to display
    if not trending_data or 'coins' not in trending_data or not trending_data['coins']:
        print_warning("No trending coins found.")
        return
    
    coins = trending_data['coins']
    
    # Create a header text
    header_text = Text("\n[bold]🔥 Trending coins on CoinGecko in the last 24 hours[/bold]\n")
    console.print(header_text)
    
    # Create a table for trending coins
    table = Table(title="CoinGecko Trending Coins")
    
    # Define table columns
    table.add_column("#", style="dim", justify="right")
    table.add_column("Name", style="cyan")
    table.add_column("Symbol", style="blue")
    table.add_column("Market Cap Rank", justify="right")
    table.add_column("BTC Price", justify="right")
    table.add_column("Score", justify="right")
    
    # Add rows to the table
    for i, coin_data in enumerate(coins, 1):
        # Get the item data
        item = coin_data.get('item', {})
        
        # Get the relevant data fields
        name = item.get('name', 'Unknown')
        symbol = item.get('symbol', '?').upper()
        market_cap_rank = str(item.get('market_cap_rank', 'N/A'))
        
        # Format the price in BTC if available
        btc_price = item.get('price_btc')
        if btc_price is not None:
            try:
                btc_price_formatted = f"₿ {float(btc_price):.8f}"
            except (ValueError, TypeError):
                btc_price_formatted = "N/A"
        else:
            btc_price_formatted = "N/A"
            
        # Get the score
        score = item.get('score')
        if score is not None:
            try:
                score_formatted = f"{int(score) + 1}"  # Add 1 as the scores are 0-based
            except (ValueError, TypeError):
                score_formatted = str(score)
        else:
            score_formatted = "N/A"
        
        # Add the row to the table
        table.add_row(
            str(i),
            name,
            symbol,
            market_cap_rank,
            btc_price_formatted,
            score_formatted
        )
    
    # Print the table
    console.print(table)
    
    # Display the last update time if available
    if 'updated_at' in trending_data:
        try:
            timestamp = trending_data['updated_at']
            dt = datetime.fromtimestamp(timestamp)
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            console.print(f"\n[dim]Last updated: {time_str}[/dim]")
        except (TypeError, ValueError):
            pass

def save_trending_data(data: Dict[str, Any], filename: Optional[str] = None) -> str:
    """
    Save trending coins data to a JSON file.
    
    Args:
        data (dict): Trending coins data
        filename (str, optional): Filename to save data to
        
    Returns:
        str: Path to the saved file
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"trending_coins_{timestamp}.json"
    
    # Ensure the filename has a .json extension
    if not filename.endswith('.json'):
        filename += '.json'
    
    # Write data to file
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    
    return os.path.abspath(filename)
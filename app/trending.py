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

"""
Functionality for retrieving and displaying trending coins and NFTs from CoinGecko.
"""
from typing import Dict, Any, List, Optional, Literal
import json
from datetime import datetime
import os

from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.console import Console

from .api import api
from .utils.formatting import (
    console, 
    print_error, 
    print_warning,
    format_currency, 
    format_large_number,
    format_percentage
)

TrendingType = Literal["coins", "nfts", "all"]

def get_trending(data_type: TrendingType = "coins", display=True, save=False, output=None):
    """
    Get and display trending cryptocurrencies or NFTs in the last 24 hours.
    
    Args:
        data_type: Type of trending data to retrieve ("coins", "nfts", or "all")
        display (bool): Whether to display the data in the console
        save (bool): Whether to save the data to a file
        output (str, optional): Filename to save data to (if save is True)
        
    Returns:
        dict: Trending data or None if an error occurs
    """
    try:
        trending_data = {}
        
        # Get trending coins if requested
        if data_type in ["coins", "all"]:
            try:
                coins_data = api.get_trending_coins()
                if coins_data and 'coins' in coins_data:
                    trending_data['coins'] = coins_data['coins']
                    if 'updated_at' in coins_data:
                        trending_data['updated_at'] = coins_data['updated_at']
            except Exception as e:
                print_error(f"Error retrieving trending coins: {str(e)}")
                trending_data['coins'] = []
        
        # Get trending NFTs if requested
        if data_type in ["nfts", "all"]:
            try:
                nfts_data = api.get_trending_nfts()
                if nfts_data and 'nfts' in nfts_data:
                    trending_data['nfts'] = nfts_data['nfts']
                    if 'updated_at' in nfts_data and 'updated_at' not in trending_data:
                        trending_data['updated_at'] = nfts_data['updated_at']
            except Exception as e:
                print_error(f"Error retrieving trending NFTs: {str(e)}")
                trending_data['nfts'] = []
        
        # Display results if requested
        if display:
            if data_type in ["coins", "all"] and 'coins' in trending_data:
                display_trending_coins(trending_data)
            
            if data_type in ["nfts", "all"] and 'nfts' in trending_data:
                display_trending_nfts(trending_data)
        
        # Save data if requested
        if save:
            file_path = save_trending_data(trending_data, data_type, output)
            console.print(f"\n[green]Trending {data_type} data saved to:[/green] {file_path}")
        
        return trending_data
    
    except Exception as e:
        print_error(f"Error retrieving trending data: {str(e)}")
        return None

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
    return get_trending("coins", display, save, output)

def get_trending_nfts(display=True, save=False, output=None):
    """
    Get and display trending NFTs in the last 24 hours.
    
    Args:
        display (bool): Whether to display the data in the console
        save (bool): Whether to save the data to a file
        output (str, optional): Filename to save data to (if save is True)
        
    Returns:
        dict: Trending NFTs data or None if an error occurs
    """
    return get_trending("nfts", display, save, output)

def display_trending_coins(trending_data: Dict[str, Any]):
    """
    Display trending cryptocurrencies in a formatted table.
    
    Args:
        trending_data (dict): Trending data from the API
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
    display_update_time(trending_data)

def display_trending_nfts(trending_data: Dict[str, Any]):
    """
    Display trending NFTs in a formatted table.
    
    Args:
        trending_data (dict): Trending data from the API
    """
    # Check if we have NFTs to display
    if not trending_data or 'nfts' not in trending_data or not trending_data['nfts']:
        print_warning("No trending NFTs found.")
        return
    
    nfts = trending_data['nfts']
    
    # Create a header text
    header_text = Text("\n[bold]🖼️ Trending NFTs on CoinGecko in the last 24 hours[/bold]\n")
    console.print(header_text)
    
    # Create a table for trending NFTs
    table = Table(title="CoinGecko Trending NFTs")
    
    # Define table columns
    table.add_column("#", style="dim", justify="right")
    table.add_column("Name", style="cyan")
    table.add_column("Symbol", style="blue")
    table.add_column("Floor Price (ETH)", justify="right")
    table.add_column("24h Volume", justify="right")
    table.add_column("Market Cap", justify="right")
    table.add_column("Score", justify="right")
    
    # Add rows to the table
    for i, nft_data in enumerate(nfts, 1):
        # Get the item data
        item = nft_data.get('item', {})
        
        # Get the relevant data fields
        name = item.get('name', 'Unknown')
        symbol = item.get('symbol', '?').upper()
        
        # Format the floor price in ETH if available
        floor_price = item.get('floor_price_in_eth')
        if floor_price is not None:
            try:
                floor_price_formatted = f"Ξ {float(floor_price):.4f}"
            except (ValueError, TypeError):
                floor_price_formatted = "N/A"
        else:
            floor_price_formatted = "N/A"
        
        # Format volume
        volume = item.get('volume_24h')
        volume_formatted = format_currency(volume, 'USD') if volume else "N/A"
        
        # Format market cap
        market_cap = item.get('market_cap')
        market_cap_formatted = format_currency(market_cap, 'USD') if market_cap else "N/A"
            
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
            floor_price_formatted,
            volume_formatted,
            market_cap_formatted,
            score_formatted
        )
    
    # Print the table
    console.print(table)
    
    # Display the last update time if available
    display_update_time(trending_data)

def display_update_time(data: Dict[str, Any]):
    """Display the last update time if available."""
    if 'updated_at' in data:
        try:
            timestamp = data['updated_at']
            dt = datetime.fromtimestamp(timestamp)
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            console.print(f"\n[dim]Last updated: {time_str}[/dim]")
        except (TypeError, ValueError):
            pass

def save_trending_data(data: Dict[str, Any], data_type: TrendingType = "all", filename: Optional[str] = None) -> str:
    """
    Save trending data to a JSON file.
    
    Args:
        data (dict): Trending data
        data_type (str): Type of trending data ("coins", "nfts", or "all")
        filename (str, optional): Filename to save data to
        
    Returns:
        str: Path to the saved file
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"trending_{data_type}_{timestamp}.json"
    
    # Ensure the filename has a .json extension
    if not filename.endswith('.json'):
        filename += '.json'
    
    # Write data to file
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    
    return os.path.abspath(filename)
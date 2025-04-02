"""
Module for retrieving and displaying asset platforms (blockchains) available on CoinGecko.
"""
from typing import Dict, List, Any, Optional
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
import json
import time
import os

from .api import api
from .utils.formatting import (
    console,
    print_error,
    print_warning,
    print_success
)

def get_asset_platforms(display: bool = True, format_type: str = 'table', query: str = None) -> List[Dict[str, Any]]:
    """
    Get a list of all asset platforms (blockchains) supported by CoinGecko.
    
    Args:
        display: Whether to display the results
        format_type: How to format the display ('table' or 'list')
        query: Optional search query to filter platforms
        
    Returns:
        List of asset platform data
    """
    try:
        # Make API request to get asset platforms
        platforms = api.get_asset_platforms()
        
        if not platforms:
            print_warning("No asset platforms found")
            return []
        
        # Filter platforms if query is provided
        if query and platforms:
            query = query.lower()
            filtered_platforms = []
            
            for platform in platforms:
                # Check if query matches id, name or chain identifier
                platform_id = platform.get('id', '').lower()
                platform_name = platform.get('name', '').lower()
                platform_chain = platform.get('chain_identifier', '')
                if platform_chain is not None:
                    platform_chain = str(platform_chain).lower()
                
                if (query in platform_id or
                    query in platform_name or
                    (platform_chain and query in platform_chain)):
                    filtered_platforms.append(platform)
            
            platforms = filtered_platforms
            
            if not platforms:
                print_warning(f"No platforms found matching '{query}'")
                return []
        
        # Sort platforms by name for better display
        platforms.sort(key=lambda x: x.get('name', '').lower())
            
        # Display the results if requested
        if display:
            if format_type.lower() == 'table':
                display_platforms_table(platforms)
            else:
                display_platforms_list(platforms)
            
        return platforms
    except Exception as e:
        print_error(f"Failed to fetch asset platforms: {str(e)}")
        return []

def display_platforms_table(platforms: List[Dict[str, Any]]) -> None:
    """
    Display asset platforms in a table format.
    
    Args:
        platforms: List of asset platform data
    """
    if not platforms:
        print_warning("No asset platforms to display")
        return
    
    # Create a table for displaying platforms
    table = Table(title="Asset Platforms (Blockchains)")
    
    # Add columns
    table.add_column("ID", style="cyan", justify="left")
    table.add_column("Name", style="bright_white", justify="left")
    table.add_column("Short Name", style="green", justify="left")
    table.add_column("Chain ID", justify="right")
    table.add_column("Has Contracts", justify="center")
    
    # Add rows for each platform
    for platform in platforms:
        platform_id = platform.get('id', 'N/A')
        name = platform.get('name', 'N/A')
        shortname = platform.get('shortname', '')
        chain_id = platform.get('chain_identifier')
        chain_id_str = str(chain_id) if chain_id is not None else "N/A"
        
        # Check if platform has contract support
        has_contracts = "✓" if platform.get('native_coin_id') else "✗"
        
        table.add_row(
            platform_id,
            name,
            shortname,
            chain_id_str,
            has_contracts
        )
    
    # Display the table
    console.print(table)
    console.print(f"\n[dim]Total platforms: {len(platforms)}[/dim]")
    
    # Print a note about how to use the platforms
    console.print("\n[dim]Note: Use the ID in the first column with the token command. For example:[/dim]")
    example_id = platforms[0].get('id', 'ethereum') if platforms else 'ethereum'
    console.print(f"[yellow]CryptoCLI token 0x1f9840a85d5af5bf1d1762f925bdaddc4201f984 --platform {example_id}[/yellow]")

def display_platforms_list(platforms: List[Dict[str, Any]]) -> None:
    """
    Display asset platforms in a simplified list format.
    
    Args:
        platforms: List of asset platform data
    """
    if not platforms:
        print_warning("No asset platforms to display")
        return
    
    console.print("[bold]Asset Platforms (Blockchains)[/bold]\n")
    
    # Create a list of platform items
    platform_texts = []
    for platform in platforms:
        platform_id = platform.get('id', 'N/A')
        name = platform.get('name', 'N/A')
        
        text = Text()
        text.append(f"{platform_id}", style="cyan")
        text.append(f" - {name}")
        
        platform_texts.append(text)
    
    # Display in columns
    columns = Columns(platform_texts, equal=True, expand=True)
    console.print(columns)
    
    console.print(f"\n[dim]Total platforms: {len(platforms)}[/dim]")

def save_platforms_data(platforms: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
    """
    Save asset platforms data to a JSON file.
    
    Args:
        platforms: List of asset platforms to save
        filename: Optional filename to save to
        
    Returns:
        Path to the saved file
    """
    if not platforms:
        print_error("No platforms data to save")
        return ""
    
    # Generate a default filename if none provided
    if not filename:
        timestamp = int(time.time())
        filename = f"asset_platforms_{timestamp}.json"
    
    try:
        # Create a data object with metadata
        data_object = {
            "count": len(platforms),
            "generated_at": int(time.time()),
            "platforms": platforms
        }
        
        # Write to file
        with open(filename, 'w') as f:
            json.dump(data_object, f, indent=4)
            
        print_success(f"Asset platforms data saved to {filename}")
        return filename
    except Exception as e:
        print_error(f"Failed to save platforms data: {str(e)}")
        return ""
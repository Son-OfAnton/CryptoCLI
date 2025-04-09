"""
Module for retrieving and displaying NFT marketplace data for collections.
"""
from typing import Dict, List, Any, Tuple, Optional
import json
import time
from datetime import datetime
import os

from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.progress import Progress

from .api import api
from .utils.formatting import (
    console,
    format_currency,
    format_large_number,
    format_price_change,
    format_percentage,
    print_error,
    print_warning,
    print_success
)

from .nft_collections import (
    get_nft_collection_by_id,
    get_nft_collection_by_contract_address,
    is_valid_contract_address
)

def get_nft_marketplace_data(
    collection_identifier: str,
    vs_currency: str = 'usd',
    is_contract_address: bool = False,
    asset_platform: str = 'ethereum',
    display: bool = True
) -> Dict[str, Any]:
    """
    Get marketplace data for an NFT collection across different marketplaces.
    
    Args:
        collection_identifier: Collection ID or contract address
        vs_currency: Currency to get data in (default: 'usd')
        is_contract_address: Whether the identifier is a contract address
        asset_platform: Asset platform if using contract address (default: 'ethereum')
        display: Whether to display the results
        
    Returns:
        Dictionary containing marketplace data for the NFT collection
    """
    try:
        # Step 1: Get the collection information
        collection_info = None
        
        if is_contract_address:
            # Validate contract address
            if not is_valid_contract_address(collection_identifier):
                print_error("Invalid contract address format.")
                return {
                    "success": False,
                    "error": "Invalid contract address format."
                }
                
            # Get collection info by contract address
            collection_info = get_nft_collection_by_contract_address(
                contract_address=collection_identifier,
                asset_platform=asset_platform,
                display=False
            )
            
            if not collection_info.get("success", False):
                return collection_info  # Return the error
                
            # Extract collection ID from the response
            collection_id = collection_info.get("collection_id")
        else:
            # Use the provided collection ID directly
            collection_id = collection_identifier
            
            # Get basic collection info
            collection_info = get_nft_collection_by_id(
                collection_id=collection_id,
                vs_currency=vs_currency,
                display=False
            )
            
            if not collection_info.get("success", False):
                return collection_info  # Return the error
        
        # Step 2: Get marketplace data for the collection
        with Progress() as progress:
            task = progress.add_task(
                f"Fetching marketplace data for {collection_info.get('collection_name', collection_id)}...", 
                total=100
            )
            
            marketplace_data = api.get_nft_collection_marketplaces(
                id=collection_id
            )
            
            progress.update(task, completed=100)
            
        # Step 3: Prepare the result
        collection_data = collection_info.get("collection", {})
        
        result = {
            "collection_id": collection_id,
            "collection_name": collection_data.get("name") or collection_info.get("collection_name", "Unknown Collection"),
            "currency": vs_currency,
            "marketplaces": marketplace_data,
            "timestamp": int(time.time()),
            "success": True
        }
        
        # Add collection details from collection_info
        if collection_data:
            result["collection"] = collection_data
        
        # If identified by contract address, include that info
        if is_contract_address:
            result["contract_address"] = collection_identifier
            result["asset_platform"] = asset_platform
            
        # Step 4: Add summary statistics across marketplaces
        result["summary"] = calculate_marketplace_summary(marketplace_data, vs_currency)
            
        # Step 5: Display the results if requested
        if display:
            display_nft_marketplace_data(result)
            
        return result
    
    except Exception as e:
        print_error(f"Failed to fetch NFT marketplace data: {str(e)}")
        return {
            "collection_identifier": collection_identifier,
            "currency": vs_currency,
            "success": False,
            "error": str(e)
        }

def calculate_marketplace_summary(marketplace_data: Dict[str, Any], currency: str = 'usd') -> Dict[str, Any]:
    """
    Calculate summary statistics across all marketplaces.
    
    Args:
        marketplace_data: Dictionary of marketplace data
        currency: Currency for calculations
        
    Returns:
        Dictionary of summary statistics
    """
    if not marketplace_data:
        return {
            "total_volume_24h": 0,
            "lowest_floor_price": 0,
            "highest_floor_price": 0,
            "avg_floor_price": 0,
            "marketplace_count": 0,
            "most_active_marketplace": "None",
            "highest_floor_marketplace": "None",
            "lowest_floor_marketplace": "None"
        }
        
    # Extract relevant data from each marketplace
    marketplace_stats = []
    currency_lower = currency.lower()
    
    for name, data in marketplace_data.items():
        floor_price = data.get("floor_price", {}).get(currency_lower, 0)
        volume_24h = data.get("volume_24h", {}).get(currency_lower, 0)
        
        if floor_price or volume_24h:  # Only include marketplaces with data
            marketplace_stats.append({
                "name": name,
                "floor_price": floor_price,
                "volume_24h": volume_24h
            })
    
    if not marketplace_stats:
        return {
            "total_volume_24h": 0,
            "lowest_floor_price": 0,
            "highest_floor_price": 0,
            "avg_floor_price": 0,
            "marketplace_count": 0,
            "most_active_marketplace": "None",
            "highest_floor_marketplace": "None",
            "lowest_floor_marketplace": "None"
        }
    
    # Calculate summary statistics
    total_volume_24h = sum(m["volume_24h"] for m in marketplace_stats)
    
    # Filter for marketplaces with non-zero floor price
    marketplaces_with_floor = [m for m in marketplace_stats if m["floor_price"] > 0]
    
    if marketplaces_with_floor:
        lowest_floor_price = min(m["floor_price"] for m in marketplaces_with_floor)
        lowest_floor_marketplace = next(m["name"] for m in marketplaces_with_floor if m["floor_price"] == lowest_floor_price)
        
        highest_floor_price = max(m["floor_price"] for m in marketplaces_with_floor)
        highest_floor_marketplace = next(m["name"] for m in marketplaces_with_floor if m["floor_price"] == highest_floor_price)
        
        avg_floor_price = sum(m["floor_price"] for m in marketplaces_with_floor) / len(marketplaces_with_floor)
    else:
        lowest_floor_price = 0
        lowest_floor_marketplace = "None"
        highest_floor_price = 0
        highest_floor_marketplace = "None"
        avg_floor_price = 0
    
    # Find most active marketplace
    if marketplace_stats:
        most_active = max(marketplace_stats, key=lambda m: m["volume_24h"])
        most_active_marketplace = most_active["name"]
    else:
        most_active_marketplace = "None"
    
    return {
        "total_volume_24h": total_volume_24h,
        "lowest_floor_price": lowest_floor_price,
        "highest_floor_price": highest_floor_price,
        "avg_floor_price": avg_floor_price,
        "marketplace_count": len(marketplace_stats),
        "most_active_marketplace": most_active_marketplace,
        "highest_floor_marketplace": highest_floor_marketplace,
        "lowest_floor_marketplace": lowest_floor_marketplace,
        "floor_price_difference_percentage": calculate_floor_price_difference(lowest_floor_price, highest_floor_price)
    }

def calculate_floor_price_difference(lowest: float, highest: float) -> float:
    """
    Calculate the percentage difference between lowest and highest floor prices.
    
    Args:
        lowest: Lowest floor price
        highest: Highest floor price
        
    Returns:
        Percentage difference
    """
    if lowest <= 0:
        return 0
        
    return ((highest - lowest) / lowest) * 100

def display_nft_marketplace_data(data: Dict[str, Any]) -> None:
    """
    Display NFT marketplace data in a formatted way.
    
    Args:
        data: Dictionary containing marketplace data
    """
    if not data or not data.get("success", False):
        return
    
    collection_name = data.get("collection_name", "Unknown Collection")
    collection_id = data.get("collection_id", "unknown")
    currency = data.get("currency", "usd").upper()
    marketplaces = data.get("marketplaces", {})
    summary = data.get("summary", {})
    
    # Create a panel for the collection overview
    marketplace_count = summary.get("marketplace_count", 0)
    
    overview_panel = Panel(
        f"Collection: [bold cyan]{collection_name}[/bold cyan] (ID: {collection_id})\n"
        f"Found on [yellow]{marketplace_count}[/yellow] marketplaces\n"
        f"Currency: [green]{currency}[/green]",
        title="NFT Marketplace Data",
        border_style="blue"
    )
    
    console.print(overview_panel)
    
    # Display summary statistics
    summary_table = Table(title="Market Summary", box=box.SIMPLE_HEAVY)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", justify="right")
    
    summary_table.add_row("Total 24h Volume", format_currency(summary.get("total_volume_24h", 0), currency.lower()))
    
    if summary.get("lowest_floor_price", 0) > 0:
        summary_table.add_row(
            f"Lowest Floor Price ([yellow]{summary.get('lowest_floor_marketplace', 'Unknown')}[/yellow])", 
            format_currency(summary.get("lowest_floor_price", 0), currency.lower())
        )
    
    if summary.get("highest_floor_price", 0) > 0:
        summary_table.add_row(
            f"Highest Floor Price ([yellow]{summary.get('highest_floor_marketplace', 'Unknown')}[/yellow])", 
            format_currency(summary.get("highest_floor_price", 0), currency.lower())
        )
    
    if summary.get("avg_floor_price", 0) > 0:
        summary_table.add_row(
            "Average Floor Price", 
            format_currency(summary.get("avg_floor_price", 0), currency.lower())
        )
    
    # Add floor price difference information
    if summary.get("floor_price_difference_percentage", 0) > 0:
        summary_table.add_row(
            "Floor Price Difference", 
            f"{summary.get('floor_price_difference_percentage', 0):.2f}%"
        )
    
    if summary.get("most_active_marketplace", "None") != "None":
        summary_table.add_row(
            "Most Active Marketplace", 
            summary.get("most_active_marketplace", "None")
        )
    
    console.print(summary_table)
    
    # Display marketplace data
    if marketplaces:
        marketplace_table = Table(title=f"Marketplace Data (in {currency})", box=box.SIMPLE)
        marketplace_table.add_column("Marketplace", style="bright_cyan")
        marketplace_table.add_column("Floor Price", justify="right")
        marketplace_table.add_column("24h Volume", justify="right")
        marketplace_table.add_column("24h Sales", justify="right")
        marketplace_table.add_column("7d Volume", justify="right")
        marketplace_table.add_column("30d Volume", justify="right")
        
        # Sort marketplaces by 24h volume (highest first)
        sorted_marketplaces = sorted(
            marketplaces.items(), 
            key=lambda x: x[1].get("volume_24h", {}).get(currency.lower(), 0),
            reverse=True
        )
        
        for name, data in sorted_marketplaces:
            # Get marketplace data
            floor_price = data.get("floor_price", {}).get(currency.lower(), 0)
            volume_24h = data.get("volume_24h", {}).get(currency.lower(), 0)
            number_of_trades_24h = data.get("number_of_trades_24h", 0)
            seven_day_volume = data.get("seven_day_volume", {}).get(currency.lower(), 0)
            thirty_day_volume = data.get("thirty_day_volume", {}).get(currency.lower(), 0)
            
            # Format the data
            floor_price_str = format_currency(floor_price, currency.lower()) if floor_price else "N/A"
            volume_24h_str = format_currency(volume_24h, currency.lower()) if volume_24h else "N/A"
            trades_24h_str = f"{number_of_trades_24h}" if number_of_trades_24h else "N/A"
            seven_day_volume_str = format_currency(seven_day_volume, currency.lower()) if seven_day_volume else "N/A"
            thirty_day_volume_str = format_currency(thirty_day_volume, currency.lower()) if thirty_day_volume else "N/A"
            
            # Apply color to highlight the lowest and highest floor prices
            if floor_price == summary.get("lowest_floor_price", 0) and floor_price > 0:
                floor_price_str = f"[green]{floor_price_str}[/green]"
            elif floor_price == summary.get("highest_floor_price", 0) and floor_price > 0:
                floor_price_str = f"[red]{floor_price_str}[/red]"
            
            # Add row to marketplace table
            marketplace_table.add_row(
                name,
                floor_price_str,
                volume_24h_str,
                trades_24h_str,
                seven_day_volume_str,
                thirty_day_volume_str
            )
                
        console.print(marketplace_table)
    
    # Add arbitrage opportunity information if significant difference exists
    if summary.get("floor_price_difference_percentage", 0) > 5 and summary.get("lowest_floor_price", 0) > 0:
        console.print("\n[bold yellow]Potential Arbitrage Opportunity[/bold yellow]")
        console.print(
            f"There's a [bold]{summary.get('floor_price_difference_percentage', 0):.2f}%[/bold] difference " 
            f"between the lowest floor price on [bold]{summary.get('lowest_floor_marketplace')}[/bold] "
            f"({format_currency(summary.get('lowest_floor_price', 0), currency.lower())}) "
            f"and the highest on [bold]{summary.get('highest_floor_marketplace')}[/bold] "
            f"({format_currency(summary.get('highest_floor_price', 0), currency.lower())})."
        )
    
    # Add timestamp information
    if "timestamp" in data:
        timestamp_str = datetime.fromtimestamp(data["timestamp"]).strftime('%Y-%m-%d %H:%M:%S')
        console.print(f"\n[dim]Data fetched at: {timestamp_str}[/dim]")
        console.print("[dim]Source: CoinGecko NFT Marketplace Data[/dim]\n")
    
    # Add a note about using contract address
    if data.get("contract_address"):
        console.print("[dim]This collection was queried using contract address: [/dim]" 
                      f"[yellow]{data.get('contract_address')}[/yellow]")

def save_nft_marketplace_data(data: Dict[str, Any], output_filename: Optional[str] = None) -> str:
    """
    Save NFT marketplace data to a JSON file.
    
    Args:
        data: Dictionary containing marketplace data
        output_filename: Custom filename to save the data to
        
    Returns:
        Path to the saved file
    """
    if not data or not data.get("success", False):
        print_error("No valid marketplace data to save.")
        return ""
    
    # Generate default filename if none provided
    if not output_filename:
        collection_id = data.get("collection_id", "unknown")
        currency = data.get("currency", "usd").lower()
        timestamp = int(time.time())
        output_filename = f"nft_{collection_id}_marketplaces_{currency}_{timestamp}.json"
    
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        
        print_success(f"NFT marketplace data saved to {output_filename}")
        return output_filename
    except Exception as e:
        print_error(f"Failed to save data: {str(e)}")
        return ""

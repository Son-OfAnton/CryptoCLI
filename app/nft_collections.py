"""
Module for retrieving and displaying NFT collection data from CoinGecko.
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

from app.api import api
from app.utils.formatting import (
    console,
    format_currency,
    format_large_number,
    format_price_change,
    format_percentage,
    print_error,
    print_warning,
    print_success
)

def get_nft_collections(
    limit: int = 100,
    vs_currency: str = 'usd',
    order: str = 'h24_volume_native_desc',
    display: bool = True
) -> Dict[str, Any]:
    """
    Get a list of NFT collections with market data.
    
    Args:
        limit: Number of collections to return (max 250)
        vs_currency: Currency to get data in (default: 'usd')
        order: Sorting criteria (default: 'h24_volume_native_desc')
        display: Whether to display the results
        
    Returns:
        Dictionary containing NFT collections data
    """
    try:
        # Ensure limit is reasonable
        if limit <= 0:
            limit = 100
        elif limit > 250:
            print_warning(f"Maximum supported limit is 250. Using limit=250 instead of {limit}.")
            limit = 250

        # Check if order is valid
        valid_orders = [
            'h24_volume_native_desc', 'h24_volume_native_asc',
            'floor_price_native_desc', 'floor_price_native_asc',
            'market_cap_native_desc', 'market_cap_native_asc',
            'market_cap_usd_desc', 'market_cap_usd_asc'
        ]
        if order not in valid_orders:
            print_warning(f"Invalid order '{order}'. Using default 'h24_volume_native_desc'.")
            order = 'h24_volume_native_desc'
            
        with Progress() as progress:
            task = progress.add_task(f"Fetching NFT collections data...", total=100)
            
            # Get NFT collections data
            collections_data = api.get_nft_collections(
                per_page=limit,
                page=1,
                order=order
            )
            
            progress.update(task, completed=100)
        
        # Prepare result
        result = {
            "collections": collections_data,
            "count": len(collections_data),
            "limit": limit,
            "currency": vs_currency,
            "order": order,
            "timestamp": int(time.time())
        }
        
        # Add some market statistics
        if collections_data:
            # Calculate total market cap and volume
            total_market_cap = sum(c.get('market_cap', {}).get(vs_currency, 0) for c in collections_data if c.get('market_cap'))
            total_volume_24h = sum(c.get('volume_24h', {}).get(vs_currency, 0) for c in collections_data if c.get('volume_24h'))
            
            # Get some basic statistics
            result["market_stats"] = {
                "total_market_cap": total_market_cap,
                "total_volume_24h": total_volume_24h,
                "average_market_cap": total_market_cap / len(collections_data) if collections_data else 0,
                "average_volume_24h": total_volume_24h / len(collections_data) if collections_data else 0,
            }
                
        # Display the results if requested
        if display:
            display_nft_collections(result)
        
        return result
    
    except Exception as e:
        print_error(f"Failed to fetch NFT collections data: {str(e)}")
        return {
            "collections": [],
            "count": 0,
            "limit": limit,
            "currency": vs_currency,
            "order": order,
            "timestamp": int(time.time()),
            "error": str(e)
        }

def get_nft_collection_by_id(
    collection_id: str,
    vs_currency: str = 'usd',
    display: bool = True
) -> Dict[str, Any]:
    """
    Get detailed information about a specific NFT collection.
    
    Args:
        collection_id: ID of the NFT collection
        vs_currency: Currency to get data in (default: 'usd')
        display: Whether to display the results
        
    Returns:
        Dictionary containing NFT collection details
    """
    try:
        # Get detailed data for the collection
        collection_data = api.get_nft_collection(collection_id)
        
        if not collection_data:
            print_error(f"NFT collection '{collection_id}' not found.")
            return {
                "success": False,
                "error": f"NFT collection '{collection_id}' not found."
            }
            
        # Get price history data if available
        try:
            price_history = api.get_nft_collection_price_history(
                collection_id,
                vs_currency=vs_currency,
                days=30
            )
        except Exception:
            price_history = []
            
        # Combine the data
        result = {
            "collection": collection_data,
            "price_history": price_history,
            "currency": vs_currency,
            "timestamp": int(time.time()),
            "success": True
        }
            
        # Display the results if requested
        if display:
            display_nft_collection_details(result)
            
        return result
    
    except Exception as e:
        print_error(f"Failed to fetch NFT collection data: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def display_nft_collections(data: Dict[str, Any]) -> None:
    """
    Display a list of NFT collections in a formatted table.
    
    Args:
        data: Dictionary containing NFT collections data
    """
    if not data or not data.get("collections"):
        print_warning("No NFT collections data to display.")
        return
    
    collections = data.get("collections", [])
    currency = data.get("currency", "usd").upper()
    count = len(collections)
    
    # Create title based on sorting order
    order = data.get("order", "h24_volume_native_desc")
    order_desc = {
        'h24_volume_native_desc': 'Highest 24h Volume',
        'h24_volume_native_asc': 'Lowest 24h Volume',
        'floor_price_native_desc': 'Highest Floor Price',
        'floor_price_native_asc': 'Lowest Floor Price',
        'market_cap_native_desc': 'Highest Market Cap',
        'market_cap_native_asc': 'Lowest Market Cap'
    }.get(order, 'Top')
    
    # Create a panel for market statistics
    market_stats = data.get("market_stats", {})
    if market_stats:
        stats_panel = Panel(
            f"Total Market Cap: [green]{format_currency(market_stats.get('total_market_cap', 0), currency.lower())}[/green]\n"
            f"Total 24h Volume: [cyan]{format_currency(market_stats.get('total_volume_24h', 0), currency.lower())}[/cyan]\n"
            f"Collections Shown: [yellow]{count}[/yellow]",
            title="NFT Market Statistics",
            border_style="blue"
        )
        console.print(stats_panel)
        console.print()
        
    # Create table for collections
    table = Table(
        title=f"{order_desc} NFT Collections (in {currency})",
        box=box.SIMPLE_HEAVY
    )
    
    # Add columns
    table.add_column("#", style="dim", justify="right")
    table.add_column("Collection", justify="left")
    table.add_column("Native Token", justify="left")
    table.add_column("Floor Price", justify="right")
    table.add_column("Market Cap", justify="right")
    table.add_column("24h Vol", justify="right")
    table.add_column("24h %", justify="right")
    table.add_column("7d %", justify="right")
    table.add_column("Owners / Items", justify="right")
    
    # Add rows
    for i, collection in enumerate(collections, 1):
        name = collection.get('name', 'Unknown')
        
        # Get native asset data
        native_token = collection.get('native_currency', 'ETH')
        
        # Get floor price (prefer vs_currency if available, otherwise use native)
        floor_price_data = collection.get('floor_price', {})
        floor_price = floor_price_data.get(currency.lower(), 
                                          floor_price_data.get('native', 0))
        floor_price_str = format_currency(floor_price, currency.lower())
        
        # Get market cap data
        market_cap_data = collection.get('market_cap', {})
        market_cap = market_cap_data.get(currency.lower(), 0)
        market_cap_str = format_large_number(market_cap)
        
        # Get volume data
        volume_data = collection.get('volume_24h', {})
        volume = volume_data.get(currency.lower(), 0)
        volume_str = format_large_number(volume)
        
        # Get price change data
        price_change_24h = collection.get('floor_price_24h_percentage_change', 0)
        price_change_7d = collection.get('floor_price_7d_percentage_change', 0)
        
        # Get additional stats
        total_supply = collection.get('total_supply', 0)
        num_owners = collection.get('number_of_unique_addresses', 0)
        ownership_ratio = f"{num_owners:,} / {total_supply:,}"
        
        # Add row
        table.add_row(
            f"{i}",
            name,
            native_token,
            floor_price_str,
            market_cap_str,
            volume_str,
            format_price_change(price_change_24h),
            format_price_change(price_change_7d),
            ownership_ratio
        )
    
    # Display the table
    console.print(table)
    
    # Add source information
    timestamp_str = datetime.fromtimestamp(data.get('timestamp', time.time())).strftime('%Y-%m-%d %H:%M:%S')
    console.print(f"\n[dim]Data fetched at: {timestamp_str}[/dim]")
    console.print("[dim]Source: CoinGecko NFT Collections Data[/dim]\n")
    
    # Add a note about how to view details
    console.print("[dim]For detailed information about a specific collection, use the 'nft-collection' command:[/dim]")
    if collections:
        example_id = collections[0].get('id', 'example-collection')
        console.print(f"[yellow]CryptoCLI nft-collection {example_id}[/yellow]")

def display_nft_collection_details(data: Dict[str, Any]) -> None:
    """
    Display detailed information about a specific NFT collection.
    
    Args:
        data: Dictionary containing NFT collection details
    """
    if not data or not data.get("success", False):
        return
    
    collection = data.get("collection", {})
    price_history = data.get("price_history", [])
    currency = data.get("currency", "usd").upper()
    
    if not collection:
        print_warning("No collection data to display.")
        return
    
    # Create a panel for the collection overview
    name = collection.get('name', 'Unknown Collection')
    description = collection.get('description', 'No description available.')
    if len(description) > 500:
        description = description[:497] + '...'
        
    # Truncate description and add ellipsis if too long
    image_url = collection.get('image', {}).get('small', '')
    
    # Get contract information
    contracts = collection.get('contract_address', [])
    contract_str = ", ".join(contracts) if contracts else "Not available"
    
    # Display the panel
    collection_panel = Panel(
        f"[bold]{name}[/bold]\n\n"
        f"{description}\n\n"
        f"[cyan]Contract Address:[/cyan] {contract_str}\n"
        f"[cyan]Blockchain:[/cyan] {collection.get('asset_platform_id', 'Unknown')}\n"
        f"[cyan]Native Currency:[/cyan] {collection.get('native_currency', 'ETH')}\n",
        title=f"NFT Collection: {name}",
        border_style="green"
    )
    
    console.print(collection_panel)
    
    # Create a table for market data
    market_table = Table(title=f"Market Data (in {currency})", box=box.SIMPLE)
    market_table.add_column("Metric", style="cyan")
    market_table.add_column("Value", justify="right")
    
    # Get market data
    floor_price_data = collection.get('floor_price', {})
    floor_price = floor_price_data.get(currency.lower(), floor_price_data.get('native', 0))
    
    market_cap_data = collection.get('market_cap', {})
    market_cap = market_cap_data.get(currency.lower(), 0)
    
    volume_data = collection.get('volume_24h', {})
    volume_24h = volume_data.get(currency.lower(), 0)
    volume_7d = collection.get('seven_day_volume', {}).get(currency.lower(), 0)
    volume_30d = collection.get('thirty_day_volume', {}).get(currency.lower(), 0)
    
    # Add market data rows
    market_table.add_row("Floor Price", format_currency(floor_price, currency.lower()))
    market_table.add_row("Market Cap", format_currency(market_cap, currency.lower()))
    market_table.add_row("24h Volume", format_currency(volume_24h, currency.lower()))
    market_table.add_row("7d Volume", format_currency(volume_7d, currency.lower()))
    market_table.add_row("30d Volume", format_currency(volume_30d, currency.lower()))
    
    # Add price change data
    price_change_24h = collection.get('floor_price_24h_percentage_change', 0)
    price_change_7d = collection.get('floor_price_7d_percentage_change', 0)
    price_change_30d = collection.get('floor_price_30d_percentage_change', 0)
    
    market_table.add_row("24h Change", format_price_change(price_change_24h))
    market_table.add_row("7d Change", format_price_change(price_change_7d))
    market_table.add_row("30d Change", format_price_change(price_change_30d))
    
    # Add collection stats
    total_supply = collection.get('total_supply', 0)
    num_owners = collection.get('number_of_unique_addresses', 0)
    
    market_table.add_row("Total Supply", f"{total_supply:,}")
    market_table.add_row("Number of Owners", f"{num_owners:,}")
    if total_supply > 0:
        ownership_percentage = (num_owners / total_supply) * 100
        market_table.add_row("Ownership Ratio", f"{ownership_percentage:.2f}%")
    
    console.print(market_table)
    
    # Display price history chart if available
    if price_history and len(price_history) > 1:
        console.print(f"\n[bold]Floor Price History (30 days in {currency})[/bold]")
        display_price_history_chart(price_history)
    
    # Display links
    console.print("\n[bold]External Links:[/bold]")
    links = collection.get('links', {})
    if links.get('homepage'):
        console.print(f"Homepage: [link={links['homepage']}]{links['homepage']}[/link]")
    if links.get('twitter'):
        console.print(f"Twitter: [link=https://twitter.com/{links['twitter']}]@{links['twitter']}[/link]")
    if links.get('discord'):
        console.print(f"Discord: {links['discord']}")
    if links.get('telegram'):
        console.print(f"Telegram: {links['telegram']}")
        
    # Add source information
    timestamp_str = datetime.fromtimestamp(data.get('timestamp', time.time())).strftime('%Y-%m-%d %H:%M:%S')
    console.print(f"\n[dim]Data fetched at: {timestamp_str}[/dim]")
    console.print("[dim]Source: CoinGecko NFT Collection Data[/dim]\n")

    # Add information about querying by contract address
    console.print("\n[dim]You can also query this collection by its contract address:[/dim]")
    contracts = collection.get('contract_address', [])
    if contracts:
        example_contract = contracts[0]
        console.print(f"[yellow]CryptoCLI nft-contract-history {example_contract}[/yellow]")

def display_price_history_chart(price_history: List, chart_width: int = 80, chart_height: int = 15) -> None:
    """
    Display a simple ASCII chart of floor price history.
    
    Args:
        price_history: List of [timestamp, price] pairs
        chart_width: Width of the chart in characters
        chart_height: Height of the chart in characters
    """
    if not price_history or len(price_history) < 2:
        return
    
    # Extract timestamps and prices
    timestamps = [entry[0] for entry in price_history]
    prices = [entry[1] for entry in price_history]
    
    # Find min and max values
    max_price = max(prices)
    min_price = min(prices)
    
    # Skip chart if all values are the same (would be a flat line)
    if max_price == min_price:
        console.print("[yellow]Price chart skipped: All values are identical.[/yellow]")
        return
    
    # Determine the number of data points to display based on chart width
    if len(prices) > chart_width:
        # If we have more data points than chart width, sample the data
        step = max(1, len(prices) // chart_width)
        prices_display = prices[::step]
        timestamps_display = timestamps[::step]
    else:
        # Otherwise use all data points
        prices_display = prices
        timestamps_display = timestamps
    
    # Calculate the character height for each price point
    normalized_prices = []
    value_range = max_price - min_price
    for p in prices_display:
        if value_range > 0:
            normalized = ((p - min_price) / value_range) * (chart_height - 1)
            normalized_prices.append(int(normalized))
        else:
            normalized_prices.append(0)
    
    # Create the chart
    chart = []
    for y in range(chart_height, 0, -1):
        line = ["│"] if y == chart_height else [" "]
        for normalized in normalized_prices:
            if normalized >= y:
                line.append("█")
            else:
                line.append(" ")
        chart.append("".join(line))
    
    # Add bottom border
    bottom_border = "└" + "─" * len(prices_display)
    chart.append(bottom_border)
    
    # Display the chart
    for line in chart:
        console.print(line)
    
    # Display y-axis labels
    console.print(f"[dim]Max: {max_price:,.4f}[/dim]")
    console.print(f"[dim]Min: {min_price:,.4f}[/dim]")
    
    # Display x-axis labels (first and last date)
    if timestamps_display:
        first_date = datetime.fromtimestamp(timestamps_display[0] // 1000).strftime('%Y-%m-%d')
        last_date = datetime.fromtimestamp(timestamps_display[-1] // 1000).strftime('%Y-%m-%d')
        console.print(f"[dim]{first_date} to {last_date}[/dim]\n")

def save_nft_collections_data(data: Dict[str, Any], output_filename: Optional[str] = None) -> str:
    """
    Save NFT collections data to a JSON file.
    
    Args:
        data: Dictionary containing NFT collections data
        output_filename: Custom filename to save the data to
        
    Returns:
        Path to the saved file
    """
    if not data:
        print_error("No data to save.")
        return ""
    
    # Generate default filename if none provided
    if not output_filename:
        order = data.get("order", "default")
        currency = data.get("currency", "usd").lower()
        timestamp = int(time.time())
        output_filename = f"nft_collections_{currency}_{order}_{timestamp}.json"
    
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        
        print_success(f"NFT collections data saved to {output_filename}")
        return output_filename
    except Exception as e:
        print_error(f"Failed to save data: {str(e)}")
        return ""

def save_nft_collection_details(data: Dict[str, Any], output_filename: Optional[str] = None) -> str:
    """
    Save detailed NFT collection data to a JSON file.
    
    Args:
        data: Dictionary containing NFT collection details
        output_filename: Custom filename to save the data to
        
    Returns:
        Path to the saved file
    """
    if not data or not data.get("success", False):
        print_error("No valid collection data to save.")
        return ""
    
    collection = data.get("collection", {})
    
    # Generate default filename if none provided
    if not output_filename:
        collection_id = collection.get("id", "unknown")
        timestamp = int(time.time())
        output_filename = f"nft_collection_{collection_id}_{timestamp}.json"
    
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        
        print_success(f"NFT collection data saved to {output_filename}")
        return output_filename
    except Exception as e:
        print_error(f"Failed to save data: {str(e)}")
        return ""
    
def get_nft_collection_historical_data(
    collection_id: str,
    days: int = 30,
    vs_currency: str = 'usd',
    display: bool = True
) -> Dict[str, Any]:
    """
    Get historical market data for a specific NFT collection.
    
    Args:
        collection_id: ID of the NFT collection
        days: Number of days of historical data to fetch (max 365)
        vs_currency: Currency to get data in (default: 'usd')
        display: Whether to display the results
        
    Returns:
        Dictionary containing historical market data for the NFT collection
    """
    try:
        # Validate days parameter
        if days <= 0:
            print_warning(f"Invalid days parameter: {days}. Using default 30 days.")
            days = 30
        elif days > 365:
            print_warning(f"Maximum supported days is 365. Using days=365 instead of {days}.")
            days = 365
            
        # First, verify the collection exists and get basic info
        collection_info = api.get_nft_collection(collection_id)
        
        if not collection_info or "id" not in collection_info:
            print_error(f"NFT collection '{collection_id}' not found.")
            return {
                "success": False,
                "error": f"NFT collection '{collection_id}' not found."
            }
            
        with Progress() as progress:
            task = progress.add_task(f"Fetching historical data for {collection_info.get('name', collection_id)}...", total=100)
            progress.update(task, completed=25)
            
            # Get floor price history
            floor_price_history = api.get_nft_collection_market_chart(
                id=collection_id,
                vs_currency=vs_currency,
                days=days,
                category="floor_price"
            )
            
            progress.update(task, completed=50)
            
            # Get market cap history
            market_cap_history = api.get_nft_collection_market_chart(
                id=collection_id,
                vs_currency=vs_currency,
                days=days,
                category="market_cap"
            )
            
            progress.update(task, completed=75)
            
            # Get 24h volume history
            volume_history = api.get_nft_collection_market_chart(
                id=collection_id,
                vs_currency=vs_currency,
                days=days,
                category="volume_24h"
            )
            
            progress.update(task, completed=100)
        
        # Create result structure
        result = {
            "collection_id": collection_id,
            "collection_name": collection_info.get('name', 'Unknown Collection'),
            "days": days,
            "currency": vs_currency,
            "floor_price_history": floor_price_history,
            "market_cap_history": market_cap_history,
            "volume_history": volume_history,
            "timestamp": int(time.time()),
            "success": True
        }
        
        # Add statistics for each dataset
        result["statistics"] = {
            "floor_price": calculate_historical_stats(floor_price_history),
            "market_cap": calculate_historical_stats(market_cap_history),
            "volume": calculate_historical_stats(volume_history)
        }
        
        # Display the results if requested
        if display:
            display_nft_historical_data(result)
            
        return result
    
    except Exception as e:
        print_error(f"Failed to fetch NFT collection historical data: {str(e)}")
        return {
            "collection_id": collection_id,
            "days": days,
            "currency": vs_currency,
            "success": False,
            "error": str(e)
        }

def calculate_historical_stats(history_data: List[List]) -> Dict[str, Any]:
    """
    Calculate statistical values from historical data.
    
    Args:
        history_data: List of [timestamp, value] pairs
        
    Returns:
        Dictionary with statistical values
    """
    if not history_data or len(history_data) < 2:
        return {
            "min": 0,
            "max": 0,
            "avg": 0,
            "median": 0,
            "change_percentage": 0,
            "volatility": 0,
            "data_points": 0
        }
    
    # Extract values from timestamps
    values = [entry[1] for entry in history_data]
    
    # Basic statistics
    min_value = min(values)
    max_value = max(values)
    avg_value = sum(values) / len(values)
    
    # Calculate median
    sorted_values = sorted(values)
    middle = len(sorted_values) // 2
    if len(sorted_values) % 2 == 0:
        median_value = (sorted_values[middle - 1] + sorted_values[middle]) / 2
    else:
        median_value = sorted_values[middle]
    
    # Calculate overall change percentage
    first_value = values[0]
    last_value = values[-1]
    if first_value > 0:
        change_percentage = ((last_value - first_value) / first_value) * 100
    else:
        change_percentage = 0
    
    # Calculate daily changes for volatility
    daily_changes_pct = []
    for i in range(1, len(values)):
        if values[i-1] > 0:
            daily_change = ((values[i] - values[i-1]) / values[i-1]) * 100
            daily_changes_pct.append(daily_change)
    
    # Calculate volatility as standard deviation of daily percentage changes
    if daily_changes_pct:
        mean_daily_change = sum(daily_changes_pct) / len(daily_changes_pct)
        sum_squared_diff = sum((x - mean_daily_change) ** 2 for x in daily_changes_pct)
        volatility = (sum_squared_diff / len(daily_changes_pct)) ** 0.5
    else:
        volatility = 0
    
    return {
        "min": min_value,
        "max": max_value,
        "avg": avg_value,
        "median": median_value,
        "change_percentage": change_percentage,
        "volatility": volatility,
        "data_points": len(values)
    }

def display_nft_historical_data(data: Dict[str, Any]) -> None:
    """
    Display historical market data for an NFT collection.
    
    Args:
        data: Dictionary containing historical market data
    """
    if not data or not data.get("success", False):
        return
    
    collection_name = data.get("collection_name", "Unknown Collection")
    collection_id = data.get("collection_id", "unknown")
    days = data.get("days", 0)
    currency = data.get("currency", "usd").upper()
    
    # Create a panel for the collection overview
    overview_panel = Panel(
        f"Collection: [bold cyan]{collection_name}[/bold cyan] (ID: {collection_id})\n"
        f"Time Period: [yellow]Past {days} days[/yellow]\n"
        f"Currency: [green]{currency}[/green]",
        title="NFT Collection Historical Data",
        border_style="blue"
    )
    
    console.print(overview_panel)
    
    # Display statistics for each dataset
    stats = data.get("statistics", {})
    
    # Floor Price Statistics
    floor_price_stats = stats.get("floor_price", {})
    if floor_price_stats:
        fp_table = Table(title=f"Floor Price Statistics (in {currency})", box=box.SIMPLE)
        fp_table.add_column("Metric", style="cyan")
        fp_table.add_column("Value", justify="right")
        
        fp_table.add_row("Minimum", format_currency(floor_price_stats.get("min", 0), currency.lower()))
        fp_table.add_row("Maximum", format_currency(floor_price_stats.get("max", 0), currency.lower()))
        fp_table.add_row("Average", format_currency(floor_price_stats.get("avg", 0), currency.lower()))
        fp_table.add_row("Median", format_currency(floor_price_stats.get("median", 0), currency.lower()))
        fp_table.add_row("Overall Change", format_price_change(floor_price_stats.get("change_percentage", 0)))
        fp_table.add_row("Volatility", f"{floor_price_stats.get('volatility', 0):.2f}%")
        
        console.print(fp_table)
    
    # Market Cap Statistics
    market_cap_stats = stats.get("market_cap", {})
    if market_cap_stats:
        mc_table = Table(title=f"Market Cap Statistics (in {currency})", box=box.SIMPLE)
        mc_table.add_column("Metric", style="cyan")
        mc_table.add_column("Value", justify="right")
        
        mc_table.add_row("Minimum", format_currency(market_cap_stats.get("min", 0), currency.lower()))
        mc_table.add_row("Maximum", format_currency(market_cap_stats.get("max", 0), currency.lower()))
        mc_table.add_row("Average", format_currency(market_cap_stats.get("avg", 0), currency.lower()))
        mc_table.add_row("Median", format_currency(market_cap_stats.get("median", 0), currency.lower()))
        mc_table.add_row("Overall Change", format_price_change(market_cap_stats.get("change_percentage", 0)))
        mc_table.add_row("Volatility", f"{market_cap_stats.get('volatility', 0):.2f}%")
        
        console.print(mc_table)
    
    # Volume Statistics
    volume_stats = stats.get("volume", {})
    if volume_stats:
        vol_table = Table(title=f"24h Volume Statistics (in {currency})", box=box.SIMPLE)
        vol_table.add_column("Metric", style="cyan")
        vol_table.add_column("Value", justify="right")
        
        vol_table.add_row("Minimum", format_currency(volume_stats.get("min", 0), currency.lower()))
        vol_table.add_row("Maximum", format_currency(volume_stats.get("max", 0), currency.lower()))
        vol_table.add_row("Average", format_currency(volume_stats.get("avg", 0), currency.lower()))
        vol_table.add_row("Median", format_currency(volume_stats.get("median", 0), currency.lower()))
        vol_table.add_row("Overall Change", format_price_change(volume_stats.get("change_percentage", 0)))
        vol_table.add_row("Volatility", f"{volume_stats.get('volatility', 0):.2f}%")
        
        console.print(vol_table)
    
    # Display charts for each dataset
    console.print(f"\n[bold]Floor Price History (past {days} days)[/bold]")
    display_historical_chart(data.get("floor_price_history", []), "Floor Price")
    
    console.print(f"\n[bold]Market Cap History (past {days} days)[/bold]")
    display_historical_chart(data.get("market_cap_history", []), "Market Cap")
    
    console.print(f"\n[bold]24h Volume History (past {days} days)[/bold]")
    display_historical_chart(data.get("volume_history", []), "Volume")
    
    # Add timestamp information
    if "timestamp" in data:
        timestamp_str = datetime.fromtimestamp(data["timestamp"]).strftime('%Y-%m-%d %H:%M:%S')
        console.print(f"\n[dim]Data fetched at: {timestamp_str}[/dim]")
        console.print("[dim]Source: CoinGecko NFT Collection Market Data[/dim]\n")

def display_historical_chart(data: List[List], title: str, chart_width: int = 80, chart_height: int = 10) -> None:
    """
    Display a simple ASCII chart of historical data.
    
    Args:
        data: List of [timestamp, value] pairs
        title: Title for the chart
        chart_width: Width of the chart in characters
        chart_height: Height of the chart in characters
    """
    if not data or len(data) < 2:
        console.print("[yellow]Insufficient data to display chart.[/yellow]")
        return
    
    # Extract timestamps and values
    timestamps = [entry[0] for entry in data]
    values = [entry[1] for entry in data]
    
    # Find min and max values
    max_value = max(values)
    min_value = min(values)
    
    # Skip chart if all values are the same (would be a flat line)
    if max_value == min_value:
        console.print("[yellow]Chart skipped: All values are identical.[/yellow]")
        return
    
    # Determine the number of data points to display based on chart width
    if len(values) > chart_width:
        # If we have more data points than chart width, sample the data
        step = max(1, len(values) // chart_width)
        values_display = values[::step]
        timestamps_display = timestamps[::step]
    else:
        # Otherwise use all data points
        values_display = values
        timestamps_display = timestamps
    
    # Calculate the character height for each value point
    normalized_values = []
    value_range = max_value - min_value
    for v in values_display:
        if value_range > 0:
            normalized = ((v - min_value) / value_range) * (chart_height - 1)
            normalized_values.append(int(normalized))
        else:
            normalized_values.append(0)
    
    # Create the chart
    chart = []
    for y in range(chart_height, 0, -1):
        line = ["│"] if y == chart_height else [" "]
        for normalized in normalized_values:
            if normalized >= y:
                line.append("█")
            else:
                line.append(" ")
        chart.append("".join(line))
    
    # Add bottom border
    bottom_border = "└" + "─" * len(values_display)
    chart.append(bottom_border)
    
    # Display the chart
    for line in chart:
        console.print(line)
    
    # Display y-axis labels
    console.print(f"[dim]Max: {max_value:,.4f}[/dim]")
    console.print(f"[dim]Min: {min_value:,.4f}[/dim]")
    
    # Display x-axis labels (first and last date)
    if timestamps_display:
        first_date = datetime.fromtimestamp(timestamps_display[0] // 1000).strftime('%Y-%m-%d')
        last_date = datetime.fromtimestamp(timestamps_display[-1] // 1000).strftime('%Y-%m-%d')
        console.print(f"[dim]{first_date} to {last_date}[/dim]")

def save_nft_historical_data(data: Dict[str, Any], output_filename: Optional[str] = None) -> str:
    """
    Save NFT collection historical data to a JSON file.
    
    Args:
        data: Dictionary containing historical market data
        output_filename: Custom filename to save the data to
        
    Returns:
        Path to the saved file
    """
    if not data or not data.get("success", False):
        print_error("No valid historical data to save.")
        return ""
    
    # Generate default filename if none provided
    if not output_filename:
        collection_id = data.get("collection_id", "unknown")
        days = data.get("days", 0)
        currency = data.get("currency", "usd").lower()
        timestamp = int(time.time())
        output_filename = f"nft_{collection_id}_history_{days}d_{currency}_{timestamp}.json"
    
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        
        print_success(f"NFT collection historical data saved to {output_filename}")
        return output_filename
    except Exception as e:
        print_error(f"Failed to save data: {str(e)}")
        return ""
    
def get_nft_collection_by_contract_address(
    contract_address: str,
    asset_platform: str = 'ethereum',
    display: bool = False
) -> Dict[str, Any]:
    """
    Get NFT collection information by contract address.
    
    Args:
        contract_address: Contract address of the NFT collection
        asset_platform: Asset platform (blockchain) the collection is on
        display: Whether to display the results
        
    Returns:
        Dictionary containing NFT collection information
    """
    try:
        # Validate contract address format
        if not contract_address.startswith('0x') or len(contract_address) != 42:
            print_error("Invalid contract address. Must be in the format: 0x...")
            return {
                "success": False,
                "error": "Invalid contract address format"
            }
            
        # Validate asset platform
        supported_platforms = [
            'ethereum', 'solana', 'polygon-pos', 'arbitrum-one', 'optimistic-ethereum', 
            'binance-smart-chain', 'fantom', 'avalanche'
        ]
        
        if asset_platform not in supported_platforms:
            print_warning(f"Unsupported asset platform: {asset_platform}. Using 'ethereum' instead.")
            asset_platform = 'ethereum'
            
        # Get collection by contract address
        with Progress() as progress:
            task = progress.add_task(f"Looking up NFT collection by contract address...", total=100)
            
            collection_data = api.get_nft_collection_by_contract(
                contract_address=contract_address,
                asset_platform=asset_platform
            )
            
            progress.update(task, completed=100)
            
        if not collection_data or "id" not in collection_data:
            print_error(f"NFT collection with contract address {contract_address} not found.")
            return {
                "success": False,
                "error": f"NFT collection with contract address {contract_address} not found."
            }
        
        # Replace the contract address validation with this more detailed version
        if not is_valid_contract_address(contract_address):
            error_msg = "Invalid contract address format. "
            if not contract_address.startswith('0x'):
                error_msg += "Address must start with '0x'. "
            if len(contract_address) != 42:
                error_msg += f"Address must be 42 characters long (currently {len(contract_address)}). "
            try:
                int(contract_address[2:], 16)
            except (ValueError, IndexError):
                error_msg += "Address must contain valid hexadecimal characters after '0x'. "
            
            print_error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "contract_address": contract_address
            }
            
        # Get the collection ID for further use
        collection_id = collection_data.get("id")
        
        result = {
            "collection_id": collection_id,
            "collection_name": collection_data.get("name", "Unknown Collection"),
            "contract_address": contract_address,
            "asset_platform": asset_platform,
            "collection_data": collection_data,
            "timestamp": int(time.time()),
            "success": True
        }
        
        if display:
            # Display collection details
            display_nft_collection_details({
                "collection": collection_data,
                "price_history": [],  # No price history here
                "currency": "usd",
                "timestamp": int(time.time()),
                "success": True
            })
            
        return result
    except Exception as e:
        print_error(f"Failed to fetch NFT collection by contract address: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def get_nft_historical_data_by_contract(
    contract_address: str,
    days: int = 30,
    asset_platform: str = 'ethereum',
    vs_currency: str = 'usd',
    display: bool = True
) -> Dict[str, Any]:
    """
    Get historical market data for an NFT collection by contract address.
    
    Args:
        contract_address: Contract address of the NFT collection
        days: Number of days of historical data to fetch (max 365)
        asset_platform: Asset platform (blockchain) the collection is on
        vs_currency: Currency to get data in (default: 'usd')
        display: Whether to display the results
        
    Returns:
        Dictionary containing historical market data for the NFT collection
    """
    try:
        # First, get collection info by contract address
        collection_info = get_nft_collection_by_contract_address(
            contract_address=contract_address,
            asset_platform=asset_platform,
            display=False
        )
        
        if not collection_info.get("success", False):
            return collection_info  # Return the error
            
        # Now get historical data using the collection ID
        collection_id = collection_info.get("collection_id")
        collection_name = collection_info.get("collection_name")
        
        console.print(f"[yellow]Found collection:[/yellow] {collection_name} (ID: {collection_id})")
        console.print(f"[yellow]Fetching historical data for the past {days} days...[/yellow]\n")
        
        # Get the historical data using the existing function
        historical_data = get_nft_collection_historical_data(
            collection_id=collection_id,
            days=days,
            vs_currency=vs_currency,
            display=display
        )
        
        # Add contract address info
        historical_data["contract_address"] = contract_address
        historical_data["asset_platform"] = asset_platform
        
        return historical_data
    
    except Exception as e:
        print_error(f"Failed to fetch NFT historical data by contract address: {str(e)}")
        return {
            "success": False,
            "contract_address": contract_address,
            "asset_platform": asset_platform,
            "days": days,
            "currency": vs_currency,
            "error": str(e)
        }
    
def is_valid_contract_address(address: str) -> bool:
    """
    Validate if a string is a properly formatted contract address.
    
    Args:
        address: Contract address to validate
        
    Returns:
        True if the address is valid, False otherwise
    """
    # Basic validation for Ethereum-style addresses
    if not address:
        return False
        
    if not address.startswith('0x'):
        return False
        
    # Most Ethereum addresses are 42 characters (0x + 40 hex chars)
    if len(address) != 42:
        return False
        
    # Check if the remaining characters are valid hex
    try:
        int(address[2:], 16)  # Try to convert to hex
        return True
    except ValueError:
        return False


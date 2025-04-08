"""
Module for retrieving and displaying newly listed coins on CoinGecko.
"""
from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta
import os
from rich.table import Table
from rich.console import Console
from rich.text import Text
from rich.style import Style
from rich.panel import Panel
from rich import box

from app.api import api
from app.utils.formatting import (
    console,
    print_error,
    print_warning,
    print_success,
    format_currency,
    format_large_number,
    format_timestamp,
    format_price_change
)

def get_newly_listed_coins(
    vs_currency: str = 'usd',
    days: int = 14,
    limit: int = 200,
    display: bool = True,
    save: bool = False,
    output: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get newly listed coins on CoinGecko.
    
    Args:
        vs_currency: Currency to display prices in (e.g., 'usd', 'eur')
        days: Maximum age in days for newly listed coins (7, 14, 30 recommended)
        limit: Maximum number of newly listed coins to display
        display: Whether to display the data in the console
        save: Whether to save the data to a JSON file
        output: Optional filename to save data to
        
    Returns:
        List of newly listed coins
    """
    try:
        # First, get the list of new coins using the dedicated endpoint
        new_coins = api._make_request("coins/list/new")
        
        if not new_coins:
            print_error("No newly listed coins found.")
            return []
            
        # Apply day filtering if specified
        if days > 0:
            cutoff_date = datetime.now() - timedelta(days=days)
            filtered_coins = []
            
            for coin in new_coins:
                # CoinGecko returns date in ISO 8601 format
                date_added = coin.get('date_added')
                if date_added:
                    try:
                        # Parse ISO 8601 date (e.g., "2023-04-06T14:45:31.834Z")
                        coin_date = datetime.fromisoformat(date_added.replace('Z', '+00:00'))
                        if coin_date >= cutoff_date:
                            filtered_coins.append(coin)
                    except (ValueError, TypeError):
                        # If date parsing fails, include the coin
                        filtered_coins.append(coin)
                else:
                    # If no date, include the coin
                    filtered_coins.append(coin)
            
            new_coins = filtered_coins
            
        # Limit the number of results if needed
        new_coins = new_coins[:limit]
        
        # For each coin in the list, we need to fetch its market data to get prices, etc.
        coins_with_market_data = []
        
        # Create batches to avoid making too many API requests at once
        batch_size = 50  # Process 50 coins at a time
        for i in range(0, len(new_coins), batch_size):
            batch = new_coins[i:i+batch_size]
            
            # Extract coin IDs for this batch
            coin_ids = [coin['id'] for coin in batch]
            
            # Fetch market data for this batch of coins
            params = {
                "vs_currency": vs_currency,
                "ids": ','.join(coin_ids),
                "order": "market_cap_desc",  # Default order
                "per_page": batch_size,
                "page": 1,
                "sparkline": "false",
                "price_change_percentage": "24h,7d"
            }
            
            batch_market_data = api._make_request("coins/markets", params)
            
            # If market data is available, merge it with the basic coin info
            if batch_market_data and isinstance(batch_market_data, list):
                # Create a mapping of coin ID to market data for easier merging
                market_data_map = {coin['id']: coin for coin in batch_market_data}
                
                for coin in batch:
                    coin_id = coin['id']
                    if coin_id in market_data_map:
                        # Enrich the coin with market data
                        enriched_coin = {**coin, **market_data_map[coin_id]}
                        coins_with_market_data.append(enriched_coin)
                    else:
                        # If no market data, just add the basic coin info
                        # Add placeholders for essential market data
                        enriched_coin = {
                            **coin,
                            'current_price': None,
                            'market_cap': None,
                            'total_volume': None,
                            'price_change_percentage_24h_in_currency': None,
                            'price_change_percentage_7d_in_currency': None
                        }
                        coins_with_market_data.append(enriched_coin)
        
        # Display data if requested
        if display:
            display_newly_listed_coins(coins_with_market_data, vs_currency, days)
        
        # Save data if requested
        if save:
            file_path = save_newly_listed_data(coins_with_market_data, vs_currency, days, output)
            console.print(f"\n[green]Newly listed coins data saved to:[/green] {file_path}")
            
        return coins_with_market_data
        
    except Exception as e:
        print_error(f"Error retrieving newly listed coins: {str(e)}")
        return []

def display_newly_listed_coins(
    coins: List[Dict[str, Any]],
    vs_currency: str = 'usd',
    days: int = 14
):
    """
    Display newly listed coins in a formatted table.
    
    Args:
        coins: List of newly listed coins
        vs_currency: Currency used for pricing
        days: Days filter that was applied
    """
    if not coins:
        print_warning("No newly listed coins to display.")
        return
    
    # Create table
    table = Table(
        title=f"🆕 Newly Listed Coins on CoinGecko (Last {days} days)" if days > 0 else "🆕 Recently Listed Coins on CoinGecko",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )
    
    # Add columns
    table.add_column("#", style="dim", width=3, justify="right")
    table.add_column("Coin", style="cyan", justify="left")
    table.add_column("Symbol", style="blue", justify="center")
    table.add_column("Listed Date", style="green", justify="center")
    table.add_column(f"Price ({vs_currency.upper()})", justify="right")
    table.add_column("24h Change", justify="right")
    table.add_column("7d Change", justify="right")
    table.add_column("Market Cap", justify="right")
    table.add_column("Volume (24h)", justify="right")
    
    # Add rows
    for i, coin in enumerate(coins, 1):
        # Get the date added
        date_added = coin.get('date_added')
        if date_added:
            try:
                # Parse ISO 8601 date
                date_obj = datetime.fromisoformat(date_added.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime('%b %d, %Y')
            except (ValueError, TypeError):
                formatted_date = "Unknown"
        else:
            formatted_date = "Unknown"
        
        # Format price changes
        change_24h = format_price_change(coin.get('price_change_percentage_24h_in_currency', 0))
        change_7d = format_price_change(coin.get('price_change_percentage_7d_in_currency', 0))
        
        # Handle cases where price data is missing
        price = coin.get('current_price')
        price_formatted = format_currency(price, vs_currency) if price is not None else "N/A"
        
        market_cap = coin.get('market_cap')
        market_cap_formatted = format_large_number(market_cap) if market_cap is not None else "N/A"
        
        volume = coin.get('total_volume')
        volume_formatted = format_large_number(volume) if volume is not None else "N/A"
        
        # Add the row
        table.add_row(
            str(i),
            coin.get('name', 'Unknown'),
            coin.get('symbol', 'N/A').upper(),
            formatted_date,
            price_formatted,
            str(change_24h) if coin.get('price_change_percentage_24h_in_currency') is not None else "N/A",
            str(change_7d) if coin.get('price_change_percentage_7d_in_currency') is not None else "N/A",
            market_cap_formatted,
            volume_formatted
        )
    
    # Print table
    console.print("\n")
    console.print(table)
    
    # Print summary and timestamp
    console.print(f"\n[bold]Total coins displayed:[/bold] {len(coins)}")
    console.print(f"[dim]Data retrieved at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")

def display_new_coin_details(coin: Dict[str, Any], vs_currency: str = 'usd'):
    """
    Display detailed information about a specific newly listed coin.
    
    Args:
        coin: Coin data dictionary
        vs_currency: Currency used for pricing
    """
    if not coin:
        print_error("No coin data provided.")
        return
    
    # Create a panel for the coin details
    content = Text()
    
    # Basic information
    content.append(f"[bold]Name:[/bold] {coin.get('name', 'Unknown')}\n")
    content.append(f"[bold]Symbol:[/bold] {coin.get('symbol', 'N/A').upper()}\n")
    content.append(f"[bold]CoinGecko ID:[/bold] {coin.get('id', 'N/A')}\n")
    
    # Listed date
    date_added = coin.get('date_added')
    if date_added:
        try:
            date_obj = datetime.fromisoformat(date_added.replace('Z', '+00:00'))
            formatted_date = date_obj.strftime('%b %d, %Y')
            days_since = (datetime.now() - date_obj).days
            content.append(f"[bold]Listed on:[/bold] {formatted_date} ({days_since} days ago)\n")
        except (ValueError, TypeError):
            content.append(f"[bold]Listed on:[/bold] {date_added}\n")
    else:
        content.append("[bold]Listed on:[/bold] Unknown\n")
    
    # Price information
    current_price = coin.get('current_price')
    if current_price is not None:
        content.append(f"[bold]Current price:[/bold] {format_currency(current_price, vs_currency)}\n")
    else:
        content.append(f"[bold]Current price:[/bold] N/A\n")
    
    # Price changes
    change_24h = coin.get('price_change_percentage_24h_in_currency')
    change_7d = coin.get('price_change_percentage_7d_in_currency')
    
    content.append(f"[bold]24h change:[/bold] ")
    if change_24h is not None:
        if change_24h > 0:
            content.append(f"+{change_24h:.2f}%\n", style="green")
        elif change_24h < 0:
            content.append(f"{change_24h:.2f}%\n", style="red")
        else:
            content.append(f"{change_24h:.2f}%\n")
    else:
        content.append("N/A\n")
    
    content.append(f"[bold]7d change:[/bold] ")
    if change_7d is not None:
        if change_7d > 0:
            content.append(f"+{change_7d:.2f}%\n", style="green")
        elif change_7d < 0:
            content.append(f"{change_7d:.2f}%\n", style="red")
        else:
            content.append(f"{change_7d:.2f}%\n")
    else:
        content.append("N/A\n")
    
    # Market data
    market_cap = coin.get('market_cap')
    if market_cap is not None:
        content.append(f"[bold]Market cap:[/bold] {format_currency(market_cap, vs_currency)}\n")
    else:
        content.append(f"[bold]Market cap:[/bold] N/A\n")
        
    volume = coin.get('total_volume')
    if volume is not None:
        content.append(f"[bold]24h volume:[/bold] {format_currency(volume, vs_currency)}\n")
    else:
        content.append(f"[bold]24h volume:[/bold] N/A\n")
    
    # High / Low
    high_24h = coin.get('high_24h')
    if high_24h is not None:
        content.append(f"[bold]24h high:[/bold] {format_currency(high_24h, vs_currency)}\n")
    else:
        content.append(f"[bold]24h high:[/bold] N/A\n")
        
    low_24h = coin.get('low_24h')
    if low_24h is not None:
        content.append(f"[bold]24h low:[/bold] {format_currency(low_24h, vs_currency)}\n")
    else:
        content.append(f"[bold]24h low:[/bold] N/A\n")
    
    # Supply information
    circ_supply = coin.get('circulating_supply')
    if circ_supply is not None:
        content.append(f"[bold]Circulating supply:[/bold] {format_large_number(circ_supply)}\n")
    else:
        content.append(f"[bold]Circulating supply:[/bold] N/A\n")
    
    max_supply = coin.get('max_supply')
    if max_supply is not None:
        content.append(f"[bold]Max supply:[/bold] {format_large_number(max_supply)}\n")
        
        # Calculate percentage of max supply in circulation
        if max_supply > 0 and circ_supply is not None:
            circulation_percentage = (circ_supply / max_supply) * 100
            content.append(f"[bold]Circulation percentage:[/bold] {circulation_percentage:.2f}%\n")
    
    total_supply = coin.get('total_supply')
    if total_supply is not None:
        content.append(f"[bold]Total supply:[/bold] {format_large_number(total_supply)}\n")
    
    # Additional information if available
    if 'platforms' in coin:
        content.append("\n[bold]Platforms:[/bold]\n")
        for platform, address in coin.get('platforms', {}).items():
            if address:  # Only show platforms with contract addresses
                content.append(f"{platform}: {address}\n")
    
    # Links
    content.append("\n[bold]Links:[/bold]\n")
    content.append(f"CoinGecko: https://www.coingecko.com/en/coins/{coin.get('id', '')}\n")
    
    # Create and display the panel
    panel = Panel(
        content,
        title=f"🔍 {coin.get('name', 'Coin')} ({coin.get('symbol', 'N/A').upper()}) Details",
        border_style="cyan",
        expand=False
    )
    
    console.print("\n")
    console.print(panel)

def save_newly_listed_data(
    coins: List[Dict[str, Any]],
    vs_currency: str = 'usd',
    days: int = 14,
    filename: Optional[str] = None
) -> str:
    """
    Save newly listed coins data to a JSON file.
    
    Args:
        coins: List of newly listed coins
        vs_currency: Currency used for pricing
        days: Days filter that was applied
        filename: Optional custom filename
        
    Returns:
        Path to the saved file
    """
    # Create data structure
    data = {
        "timestamp": datetime.now().isoformat(),
        "vs_currency": vs_currency,
        "days_filter": days,
        "total_coins": len(coins),
        "coins": coins
    }
    
    # Generate filename if not provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"newly_listed_coins_{days}d_{timestamp}.json"
    
    # Ensure filename has .json extension
    if not filename.endswith('.json'):
        filename += '.json'
    
    # Save to file
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    
    return os.path.abspath(filename)

def get_detailed_analysis(coins: List[Dict[str, Any]], vs_currency: str = 'usd'):
    """
    Generate a detailed analysis of newly listed coins.
    
    Args:
        coins: List of newly listed coins
        vs_currency: Currency used for pricing
    """
    if not coins:
        print_warning("No coins available for analysis.")
        return
    
    console.print("\n[bold cyan]📊 Newly Listed Coins - Statistical Analysis[/bold cyan]")
    
    # Calculate metrics
    total_coins = len(coins)
    
    # Price statistics
    coins_with_price = [coin for coin in coins if coin.get('current_price') is not None and coin.get('current_price', 0) > 0]
    if coins_with_price:
        avg_price = sum(coin.get('current_price', 0) for coin in coins_with_price) / len(coins_with_price)
        median_price = sorted(coins_with_price, key=lambda x: x.get('current_price', 0))[len(coins_with_price) // 2].get('current_price', 0)
        min_price = min(coin.get('current_price', 0) for coin in coins_with_price)
        max_price = max(coin.get('current_price', 0) for coin in coins_with_price)
        
        console.print(f"\n[bold]Price Statistics ({vs_currency.upper()}):[/bold]")
        console.print(f"Average price: {format_currency(avg_price, vs_currency)}")
        console.print(f"Median price: {format_currency(median_price, vs_currency)}")
        console.print(f"Minimum price: {format_currency(min_price, vs_currency)}")
        console.print(f"Maximum price: {format_currency(max_price, vs_currency)}")
    
    # Market cap statistics
    coins_with_market_cap = [coin for coin in coins if coin.get('market_cap') is not None and coin.get('market_cap', 0) > 0]
    if coins_with_market_cap:
        avg_market_cap = sum(coin.get('market_cap', 0) for coin in coins_with_market_cap) / len(coins_with_market_cap)
        median_market_cap = sorted(coins_with_market_cap, key=lambda x: x.get('market_cap', 0))[len(coins_with_market_cap) // 2].get('market_cap', 0)
        min_market_cap = min(coin.get('market_cap', 0) for coin in coins_with_market_cap)
        max_market_cap = max(coin.get('market_cap', 0) for coin in coins_with_market_cap)
        
        console.print(f"\n[bold]Market Cap Statistics ({vs_currency.upper()}):[/bold]")
        console.print(f"Average market cap: {format_currency(avg_market_cap, vs_currency)}")
        console.print(f"Median market cap: {format_currency(median_market_cap, vs_currency)}")
        console.print(f"Minimum market cap: {format_currency(min_market_cap, vs_currency)}")
        console.print(f"Maximum market cap: {format_currency(max_market_cap, vs_currency)}")
    
    # Price change statistics
    coins_with_change_24h = [coin for coin in coins if coin.get('price_change_percentage_24h_in_currency') is not None]
    if coins_with_change_24h:
        avg_change_24h = sum(coin.get('price_change_percentage_24h_in_currency', 0) for coin in coins_with_change_24h) / len(coins_with_change_24h)
        positive_24h = sum(1 for coin in coins_with_change_24h if coin.get('price_change_percentage_24h_in_currency', 0) > 0)
        negative_24h = sum(1 for coin in coins_with_change_24h if coin.get('price_change_percentage_24h_in_currency', 0) < 0)
        unchanged_24h = len(coins_with_change_24h) - positive_24h - negative_24h
        
        console.print(f"\n[bold]24-Hour Price Change Statistics:[/bold]")
        console.print(f"Average change: {format_price_change(avg_change_24h)}")
        console.print(f"Coins with positive change: {positive_24h} ({positive_24h/len(coins_with_change_24h)*100:.1f}%)")
        console.print(f"Coins with negative change: {negative_24h} ({negative_24h/len(coins_with_change_24h)*100:.1f}%)")
        console.print(f"Coins with no change: {unchanged_24h} ({unchanged_24h/len(coins_with_change_24h)*100:.1f}%)")
    
    coins_with_change_7d = [coin for coin in coins if coin.get('price_change_percentage_7d_in_currency') is not None]
    if coins_with_change_7d:
        avg_change_7d = sum(coin.get('price_change_percentage_7d_in_currency', 0) for coin in coins_with_change_7d) / len(coins_with_change_7d)
        positive_7d = sum(1 for coin in coins_with_change_7d if coin.get('price_change_percentage_7d_in_currency', 0) > 0)
        negative_7d = sum(1 for coin in coins_with_change_7d if coin.get('price_change_percentage_7d_in_currency', 0) < 0)
        unchanged_7d = len(coins_with_change_7d) - positive_7d - negative_7d
        
        console.print(f"\n[bold]7-Day Price Change Statistics:[/bold]")
        console.print(f"Average change: {format_price_change(avg_change_7d)}")
        console.print(f"Coins with positive change: {positive_7d} ({positive_7d/len(coins_with_change_7d)*100:.1f}%)")
        console.print(f"Coins with negative change: {negative_7d} ({negative_7d/len(coins_with_change_7d)*100:.1f}%)")
        console.print(f"Coins with no change: {unchanged_7d} ({unchanged_7d/len(coins_with_change_7d)*100:.1f}%)")
    
    # Listing date distribution
    coins_with_dates = [coin for coin in coins if coin.get('date_added')]
    if coins_with_dates:
        # Parse dates and count by day
        date_counts = {}
        for coin in coins_with_dates:
            try:
                date_obj = datetime.fromisoformat(coin.get('date_added', '').replace('Z', '+00:00'))
                date_str = date_obj.strftime('%Y-%m-%d')
                if date_str in date_counts:
                    date_counts[date_str] += 1
                else:
                    date_counts[date_str] = 1
            except (ValueError, TypeError):
                pass
        
        console.print(f"\n[bold]Listing Date Distribution:[/bold]")
        sorted_dates = sorted(date_counts.items(), key=lambda x: x[0], reverse=True)
        for date_str, count in sorted_dates[:10]:  # Show the 10 most recent dates
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                friendly_date = date_obj.strftime('%b %d, %Y')
                console.print(f"{friendly_date}: {count} coins")
            except (ValueError, TypeError):
                console.print(f"{date_str}: {count} coins")
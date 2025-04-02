"""
Module for retrieving and displaying token metadata and market data by contract address.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
import json
import os
import time

from .api import api
from .utils.formatting import (
    console,
    format_currency,
    format_large_number,
    format_price_change,
    format_timestamp,
    print_error,
    print_warning,
    print_success
)

def get_token_by_contract(
    contract_address: str, 
    asset_platform: str = 'ethereum',
    vs_currency: str = 'usd',
    display: bool = True
) -> Dict[str, Any]:
    """
    Get comprehensive metadata and market data for a token by its contract address.
    
    Args:
        contract_address: Contract address of the token
        asset_platform: Asset platform ID (ethereum, binance-smart-chain, etc.)
        vs_currency: Currency to display market data in
        display: Whether to display the results
        
    Returns:
        Dictionary containing token metadata and market data
    """
    try:
        # Make API request to get token data by contract address
        token_data = api.get_token_by_contract(
            contract_address=contract_address,
            asset_platform=asset_platform
        )
        
        if not token_data:
            print_warning(f"No token found with contract address {contract_address} on {asset_platform}")
            return {}
        
        # Store the asset platform and contract address in the response for reference
        token_data["asset_platform"] = asset_platform
        token_data["contract_address"] = contract_address
            
        # Display the results if requested
        if display:
            display_token_metadata(token_data)
            display_token_market_data(token_data, vs_currency)
            
        return token_data
    except Exception as e:
        print_error(f"Failed to fetch token data: {str(e)}")
        return {}

def display_token_metadata(token_data: Dict[str, Any]) -> None:
    """
    Display token metadata in a formatted way.
    
    Args:
        token_data: Token data from the API
    """
    if not token_data:
        print_warning("No token metadata to display")
        return
    
    # Extract token identification info
    token_id = token_data.get('id', 'N/A')
    token_name = token_data.get('name', 'Unknown Token')
    token_symbol = token_data.get('symbol', '').upper()
    asset_platform = token_data.get('asset_platform', 'unknown platform')
    contract_address = token_data.get('contract_address', 'N/A')
    
    # Print token header
    console.print(f"[bold cyan]{token_name} ({token_symbol})[/bold cyan]")
    console.print(f"ID: [cyan]{token_id}[/cyan]")
    console.print(f"Platform: [green]{asset_platform}[/green]")
    console.print(f"Contract: [yellow]{contract_address}[/yellow]")
    console.print()
    
    # Create a table for token metadata
    table = Table(title="Token Metadata")
    
    # Add columns
    table.add_column("Property", style="cyan", justify="left")
    table.add_column("Value", justify="left")
    
    # Add basic token info rows
    categories = token_data.get('categories', [])
    table.add_row("Categories", ", ".join(categories) if categories else "N/A")
    
    # Add links
    links = token_data.get('links', {})
    
    # Add homepage
    homepages = links.get('homepage', [])
    homepage_str = homepages[0] if homepages and homepages[0] != "" else "N/A"
    table.add_row("Homepage", homepage_str)
    
    # Add blockchain explorers
    explorers = links.get('blockchain_site', [])
    explorer_str = explorers[0] if explorers and explorers[0] != "" else "N/A"
    table.add_row("Explorer", explorer_str)
    
    # Add social media links
    twitter = links.get('twitter_screen_name', '')
    telegram = links.get('telegram_channel_identifier', '')
    reddit = links.get('subreddit_url', '')
    
    if twitter:
        table.add_row("Twitter", f"https://twitter.com/{twitter}")
    if telegram:
        table.add_row("Telegram", f"https://t.me/{telegram}")
    if reddit:
        table.add_row("Reddit", reddit)
    
    # Add image if available
    images = token_data.get('image', {})
    if images:
        thumb = images.get('thumb', '')
        small = images.get('small', '')
        large = images.get('large', '')
        image_url = large or small or thumb
        if image_url:
            table.add_row("Image URL", image_url)
    
    # Display the table
    console.print(table)
    
    # Print token description if available
    description = token_data.get('description', {}).get('en', '')
    if description:
        console.print("\n[bold]Description:[/bold]")
        # Use a limited length for the description to avoid overwhelming output
        max_desc_length = 500
        if len(description) > max_desc_length:
            description = description[:max_desc_length] + "... (truncated)"
        try:
            # Try to render as markdown, fall back to plain text if it fails
            console.print(Markdown(description))
        except:
            console.print(description)

def display_token_market_data(token_data: Dict[str, Any], vs_currency: str = 'usd') -> None:
    """
    Display token market data in a formatted way.
    
    Args:
        token_data: Token data from the API
        vs_currency: Currency to display market data in
    """
    if not token_data:
        print_warning("No token market data to display")
        return
    
    # Get market data
    market_data = token_data.get('market_data', {})
    if not market_data:
        print_warning("Market data not available for this token")
        return
    
    # Create a table for market data
    table = Table(title=f"Market Data ({vs_currency.upper()})")
    
    # Add columns
    table.add_column("Metric", style="cyan", justify="left")
    table.add_column("Value", justify="right")
    
    # Current price
    current_price = market_data.get('current_price', {}).get(vs_currency)
    if current_price is not None:
        table.add_row("Current Price", format_currency(current_price, vs_currency))
    
    # Market cap
    market_cap = market_data.get('market_cap', {}).get(vs_currency)
    if market_cap:
        table.add_row("Market Cap", format_large_number(market_cap))
    
    # 24h trading volume
    volume = market_data.get('total_volume', {}).get(vs_currency)
    if volume:
        table.add_row("24h Volume", format_large_number(volume))
    
    # Market cap rank
    rank = market_data.get('market_cap_rank')
    if rank:
        table.add_row("Market Cap Rank", f"#{rank}")
    
    # Price changes
    price_change_24h = market_data.get('price_change_percentage_24h', 0)
    price_change_7d = market_data.get('price_change_percentage_7d', 0)
    price_change_30d = market_data.get('price_change_percentage_30d', 0)
    
    table.add_row("Price Change (24h)", format_price_change(price_change_24h))
    table.add_row("Price Change (7d)", format_price_change(price_change_7d))
    table.add_row("Price Change (30d)", format_price_change(price_change_30d))
    
    # All-time high data
    ath = market_data.get('ath', {}).get(vs_currency)
    ath_change = market_data.get('ath_change_percentage', {}).get(vs_currency)
    ath_date = market_data.get('ath_date', {}).get(vs_currency)
    
    if ath is not None:
        table.add_row("All-Time High", format_currency(ath, vs_currency))
        
    if ath_change is not None:
        table.add_row("ATH Change %", format_price_change(ath_change))
        
    if ath_date:
        ath_date_obj = datetime.fromisoformat(ath_date.replace('Z', '+00:00'))
        table.add_row("ATH Date", ath_date_obj.strftime('%Y-%m-%d %H:%M:%S'))
    
    # Supply information
    circulating_supply = market_data.get('circulating_supply')
    total_supply = market_data.get('total_supply')
    max_supply = market_data.get('max_supply')
    
    if circulating_supply:
        table.add_row("Circulating Supply", format_large_number(circulating_supply))
    
    if total_supply:
        table.add_row("Total Supply", format_large_number(total_supply))
        
    if max_supply:
        table.add_row("Max Supply", format_large_number(max_supply))
    
    # Display the table
    console.print(table)

def display_token_exchange_tickers(token_data: Dict[str, Any], limit: int = 5) -> None:
    """
    Display token exchange tickers in a formatted way.
    
    Args:
        token_data: Token data from the API
        limit: Maximum number of tickers to display
    """
    tickers = token_data.get('tickers', [])
    
    if not tickers:
        print_warning("No exchange ticker data available")
        return
    
    # Create a table for exchange tickers
    table = Table(title=f"Top {min(limit, len(tickers))} Exchange Tickers")
    
    # Add columns
    table.add_column("Exchange", style="cyan", justify="left")
    table.add_column("Pair", justify="left")
    table.add_column("Price", justify="right")
    table.add_column("Volume (24h)", justify="right")
    table.add_column("Trust Score", justify="center")
    
    # Sort tickers by volume (descending)
    sorted_tickers = sorted(tickers, key=lambda x: x.get('volume', 0), reverse=True)
    
    # Add rows for each ticker (up to the limit)
    for ticker in sorted_tickers[:limit]:
        exchange = ticker.get('market', {}).get('name', 'Unknown')
        pair = ticker.get('base', '') + '/' + ticker.get('target', '')
        price = ticker.get('last', 0)
        volume = ticker.get('volume', 0)
        trust_score = ticker.get('trust_score', None)
        
        # Format trust score with color
        if trust_score == 'green':
            trust_display = "[green]●[/green]"
        elif trust_score == 'yellow':
            trust_display = "[yellow]●[/yellow]"
        elif trust_score == 'red':
            trust_display = "[red]●[/red]"
        else:
            trust_display = "○"
        
        table.add_row(
            exchange,
            pair,
            f"${price:,.8f}" if price < 0.01 else f"${price:,.2f}",
            format_large_number(volume),
            trust_display
        )
    
    # Display the table
    console.print(table)

def save_token_data(
    token_data: Dict[str, Any],
    filename: Optional[str] = None
) -> str:
    """
    Save token data to a JSON file.
    
    Args:
        token_data: Token data to save
        filename: Optional filename to save to
        
    Returns:
        Path to the saved file
    """
    if not token_data:
        print_error("No token data to save")
        return ""
    
    # Generate a default filename if none provided
    if not filename:
        token_name = token_data.get('symbol', 'token').lower()
        platform = token_data.get('asset_platform', 'unknown')
        timestamp = int(time.time())
        filename = f"{token_name}_{platform}_token_data_{timestamp}.json"
    
    try:
        # Create a data object with metadata
        data_object = {
            "token_id": token_data.get('id'),
            "name": token_data.get('name'),
            "symbol": token_data.get('symbol'),
            "contract_address": token_data.get('contract_address'),
            "asset_platform": token_data.get('asset_platform'),
            "generated_at": int(time.time()),
            "data": token_data
        }
        
        # Write to file
        with open(filename, 'w') as f:
            json.dump(data_object, f, indent=4)
            
        print_success(f"Token data saved to {filename}")
        return filename
    except Exception as e:
        print_error(f"Failed to save token data: {str(e)}")
        return ""
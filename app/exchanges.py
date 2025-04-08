"""
Module for retrieving and displaying information about exchanges on CoinGecko.
"""
from typing import Dict, List, Any, Optional
import json
import os
from datetime import datetime
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.box import ROUNDED
from rich.progress import Progress, TextColumn, BarColumn, SpinnerColumn

from app.api import api
from app.utils.formatting import (
    console,
    print_error,
    print_warning,
    print_success,
    format_currency,
    format_large_number
)

def get_exchanges(
    limit: int = 100,
    display: bool = True,
    filter_by: Optional[str] = None,
    sort_by: str = "trust_score",
    save: bool = False,
    output: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get a list of exchanges with active trading volumes on CoinGecko.
    
    Args:
        limit: Maximum number of exchanges to fetch (default: 100)
        display: Whether to display the data in the console
        filter_by: Optional filter to search exchange names, IDs, or countries
        sort_by: Field to sort by (trust_score, volume_24h, name, country)
        save: Whether to save the data to a JSON file
        output: Optional filename to save data to
    
    Returns:
        List of exchanges data
    """
    try:
        # Initialize progress display
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            # Create task
            task = progress.add_task("[cyan]Fetching exchanges data...", total=1)
            
            # Fetch exchanges data
            response = api._make_request("exchanges")
            
            # Update progress
            progress.update(task, advance=0.5)
            
            # Fetch global market data to get total market volume
            global_data = api.get_global_data()
            
            # Update progress
            progress.update(task, completed=1)
    
        if not response or not isinstance(response, list):
            print_error("Failed to retrieve exchanges data.")
            return []
        
        # Process exchanges data
        exchanges_data = response
        
        # Apply filter if provided
        if filter_by:
            filtered_exchanges = []
            filter_by = filter_by.lower()
            for exchange in exchanges_data:
                name = exchange.get('name', '').lower()
                exchange_id = exchange.get('id', '').lower()
                country = exchange.get('country', '').lower()
                
                if (filter_by in name or filter_by in exchange_id or 
                    (country and filter_by in country)):
                    filtered_exchanges.append(exchange)
            exchanges_data = filtered_exchanges
        
        # Apply sorting
        if sort_by == "trust_score":
            exchanges_data.sort(key=lambda x: x.get('trust_score', 0), reverse=True)
        elif sort_by == "volume_24h":
            exchanges_data.sort(key=lambda x: x.get('trade_volume_24h_btc', 0), reverse=True)
        elif sort_by == "name":
            exchanges_data.sort(key=lambda x: x.get('name', '').lower())
        elif sort_by == "country":
            # Sort by country then by name for exchanges with the same country
            exchanges_data.sort(key=lambda x: (x.get('country', 'ZZZ').lower(), x.get('name', '').lower()))
        
        # Apply limit
        exchanges_data = exchanges_data[:limit]
        
        # Add market share information if global data is available
        total_volume = 0
        if global_data and 'total_volume' in global_data:
            # Extract the total BTC trading volume
            total_volume = global_data.get('total_volume', {}).get('btc', 0)
        
        if total_volume > 0:
            for exchange in exchanges_data:
                exchange_volume = exchange.get('trade_volume_24h_btc', 0)
                market_share = (exchange_volume / total_volume) * 100 if total_volume > 0 else 0
                exchange['market_share'] = market_share
        
        # Display data if requested
        if display:
            display_exchanges(exchanges_data, len(exchanges_data), filter_by, sort_by)
        
        # Save data if requested
        if save:
            file_path = save_exchanges_data(exchanges_data, filter_by, sort_by, output)
            console.print(f"\n[green]Exchanges data saved to:[/green] {file_path}")
        
        return exchanges_data
    
    except Exception as e:
        print_error(f"Error retrieving exchanges data: {str(e)}")
        return []

def get_exchange_details(
    exchange_id: str,
    display: bool = True,
    save: bool = False,
    output: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get detailed information about a specific exchange.
    
    Args:
        exchange_id: ID of the exchange
        display: Whether to display the data in the console
        save: Whether to save the data to a JSON file
        output: Optional filename to save data to
    
    Returns:
        Dictionary containing exchange details
    """
    try:
        # Fetch exchange details
        endpoint = f"exchanges/{exchange_id}"
        exchange_data = api._make_request(endpoint)
        
        if not exchange_data:
            print_error(f"Failed to retrieve data for exchange: {exchange_id}")
            return {}
        
        # Display data if requested
        if display:
            display_exchange_details(exchange_data)
        
        # Save data if requested
        if save:
            file_path = save_exchange_details(exchange_data, output)
            console.print(f"\n[green]Exchange details saved to:[/green] {file_path}")
        
        return exchange_data
    
    except Exception as e:
        print_error(f"Error retrieving exchange details: {str(e)}")
        return {}

def display_exchanges(
    exchanges_data: List[Dict[str, Any]], 
    total_count: int,
    filter_by: Optional[str] = None,
    sort_by: str = "trust_score"
) -> None:
    """
    Display a list of exchanges in a formatted table.
    
    Args:
        exchanges_data: List of exchanges data
        total_count: Total number of exchanges being displayed
        filter_by: Filter term that was applied
        sort_by: Field that was used for sorting
    """
    if not exchanges_data:
        print_warning("No exchanges found that match the criteria.")
        return
    
    # Create table title based on filters and sorting
    title = f"📊 Cryptocurrency Exchanges"
    if filter_by:
        title += f" matching '{filter_by}'"
    
    sort_display = {
        "trust_score": "Trust Score",
        "volume_24h": "Trading Volume (24h)",
        "name": "Name",
        "country": "Country"
    }.get(sort_by, sort_by.title())
    
    title += f" (Sorted by {sort_display})"
    
    # Create a table for displaying the exchanges
    table = Table(title=title, box=ROUNDED)
    
    # Add columns
    table.add_column("#", justify="right", style="dim", no_wrap=True)
    table.add_column("Name", style="cyan")
    table.add_column("Country", style="green")
    table.add_column("Year Est.", justify="center")
    table.add_column("Trust Score", justify="center")
    table.add_column("Volume (24h BTC)", justify="right")
    table.add_column("Market Share", justify="right")
    table.add_column("URL", style="blue")
    
    # Add rows
    for i, exchange in enumerate(exchanges_data, 1):
        name = exchange.get('name', 'Unknown')
        country = exchange.get('country', 'N/A')
        year_established = str(exchange.get('year_established', 'N/A'))
        trust_score = exchange.get('trust_score', 0)
        
        # Format trust score with color based on value
        if trust_score >= 8:
            trust_score_display = f"[green]{trust_score}/10[/green]"
        elif trust_score >= 6:
            trust_score_display = f"[yellow]{trust_score}/10[/yellow]"
        else:
            trust_score_display = f"[red]{trust_score}/10[/red]"
        
        # Format volume
        volume_24h = exchange.get('trade_volume_24h_btc', 0)
        volume_display = f"₿ {volume_24h:,.2f}" if volume_24h else "N/A"
        
        # Format market share
        market_share = exchange.get('market_share', 0)
        market_share_display = f"{market_share:.2f}%" if market_share else "N/A"
        
        # Format URL
        url = exchange.get('url', '')
        url_display = url if url else "N/A"
        
        table.add_row(
            str(i),
            name,
            country,
            year_established,
            trust_score_display,
            volume_display,
            market_share_display,
            url_display
        )
    
    # Display the table
    console.print("\n")
    console.print(table)
    
    # Display total count
    console.print(f"\n[bold]Total Exchanges:[/bold] {len(exchanges_data)}")
    
    # Display timestamp
    console.print(f"[dim]Data retrieved at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")

def display_exchange_details(exchange_data: Dict[str, Any]) -> None:
    """
    Display detailed information about a specific exchange.
    
    Args:
        exchange_data: Dictionary containing exchange details
    """
    if not exchange_data:
        print_warning("No exchange details available.")
        return
    
    # Extract basic information
    name = exchange_data.get('name', 'Unknown Exchange')
    exchange_id = exchange_data.get('id', 'unknown')
    country = exchange_data.get('country', 'N/A')
    year_established = exchange_data.get('year_established', 'N/A')
    url = exchange_data.get('url', 'N/A')
    image = exchange_data.get('image', '')
    trust_score = exchange_data.get('trust_score', 0)
    trust_score_rank = exchange_data.get('trust_score_rank', 'N/A')
    has_trading_incentive = exchange_data.get('has_trading_incentive', False)
    
    # Format trust score with color
    if trust_score >= 8:
        trust_score_display = f"[green]{trust_score}/10[/green]"
    elif trust_score >= 6:
        trust_score_display = f"[yellow]{trust_score}/10[/yellow]"
    else:
        trust_score_display = f"[red]{trust_score}/10[/red]"
    
    # Create header panel
    header_text = Text()
    header_text.append(f"\n[bold]ID:[/bold] {exchange_id}\n")
    header_text.append(f"[bold]Country:[/bold] {country}\n")
    header_text.append(f"[bold]Year Established:[/bold] {year_established}\n")
    header_text.append(f"[bold]Website:[/bold] {url}\n")
    header_text.append(f"[bold]Trust Score:[/bold] {trust_score_display}\n")
    header_text.append(f"[bold]Trust Score Rank:[/bold] {trust_score_rank}\n")
    header_text.append(f"[bold]Trading Incentives:[/bold] {'Yes' if has_trading_incentive else 'No'}\n")
    
    header_panel = Panel(
        header_text,
        title=f"🏢 {name}",
        border_style="cyan",
        box=ROUNDED,
        padding=(1, 2)
    )
    
    console.print("\n")
    console.print(header_panel)
    
    # Display trading volume data if available
    if 'trade_volume_24h_btc' in exchange_data:
        volume_24h = exchange_data.get('trade_volume_24h_btc', 0)
        volume_display = f"₿ {volume_24h:,.2f}" if volume_24h else "N/A"
        console.print(f"\n[bold]24h Trading Volume:[/bold] {volume_display}")
    
    # Display social media links if available
    if 'facebook_url' in exchange_data or 'twitter_handle' in exchange_data or 'telegram_url' in exchange_data or 'reddit_url' in exchange_data:
        console.print("\n[bold]Social Media:[/bold]")
        
        if exchange_data.get('facebook_url'):
            console.print(f"Facebook: {exchange_data['facebook_url']}")
            
        if exchange_data.get('twitter_handle'):
            console.print(f"Twitter: https://twitter.com/{exchange_data['twitter_handle']}")
            
        if exchange_data.get('telegram_url'):
            console.print(f"Telegram: {exchange_data['telegram_url']}")
            
        if exchange_data.get('reddit_url'):
            console.print(f"Reddit: {exchange_data['reddit_url']}")
    
    # Display tickers/markets if available
    if 'tickers' in exchange_data and exchange_data['tickers']:
        tickers = exchange_data['tickers']
        
        # Create table for tickers
        tickers_table = Table(title=f"📈 Top Trading Pairs on {name}", box=ROUNDED)
        
        # Add columns
        tickers_table.add_column("Pair", style="cyan")
        tickers_table.add_column("Price (USD)", justify="right")
        tickers_table.add_column("Volume (24h)", justify="right")
        tickers_table.add_column("Spread", justify="right")
        tickers_table.add_column("Last Traded", justify="right")
        
        # Limit to top 10 tickers by volume
        tickers.sort(key=lambda x: x.get('volume', 0), reverse=True)
        top_tickers = tickers[:10]
        
        # Add rows
        for ticker in top_tickers:
            base = ticker.get('base', '')
            target = ticker.get('target', '')
            pair = f"{base}/{target}"
            
            last_price_usd = ticker.get('converted_last', {}).get('usd', 'N/A')
            last_price_display = f"${last_price_usd:,.8f}" if isinstance(last_price_usd, (int, float)) else "N/A"
            
            volume = ticker.get('converted_volume', {}).get('usd', 0)
            volume_display = format_currency(volume, 'usd') if volume else "N/A"
            
            bid_ask_spread = ticker.get('bid_ask_spread_percentage', 'N/A')
            spread_display = f"{bid_ask_spread:.2f}%" if isinstance(bid_ask_spread, (int, float)) else "N/A"
            
            last_traded = ticker.get('last_traded_at', '')
            if last_traded:
                try:
                    last_traded_datetime = datetime.fromisoformat(last_traded.replace('Z', '+00:00'))
                    last_traded_display = last_traded_datetime.strftime('%Y-%m-%d %H:%M')
                except (ValueError, TypeError):
                    last_traded_display = "N/A"
            else:
                last_traded_display = "N/A"
            
            tickers_table.add_row(
                pair,
                last_price_display,
                volume_display,
                spread_display,
                last_traded_display
            )
        
        console.print("\n")
        console.print(tickers_table)
    
    # Display status update if available
    if 'status_updates' in exchange_data and exchange_data['status_updates']:
        status = exchange_data['status_updates'][0]
        status_desc = status.get('description', '')
        status_date = status.get('created_at', '')
        
        if status_desc and status_date:
            try:
                status_datetime = datetime.fromisoformat(status_date.replace('Z', '+00:00'))
                status_display = status_datetime.strftime('%Y-%m-%d %H:%M')
            except (ValueError, TypeError):
                status_display = status_date
                
            status_panel = Panel(
                status_desc,
                title=f"Latest Status Update ({status_display})",
                border_style="yellow",
                box=ROUNDED
            )
            
            console.print("\n")
            console.print(status_panel)
    
    # Display timestamp
    console.print(f"\n[dim]Data retrieved at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")

def save_exchanges_data(
    exchanges_data: List[Dict[str, Any]],
    filter_by: Optional[str] = None,
    sort_by: str = "trust_score",
    filename: Optional[str] = None
) -> str:
    """
    Save exchanges data to a JSON file.
    
    Args:
        exchanges_data: List of exchanges data
        filter_by: Filter that was applied
        sort_by: Field used for sorting
        filename: Optional filename to save data to
        
    Returns:
        Path to the saved file
    """
    if not exchanges_data:
        print_error("No data to save.")
        return ""
    
    # Generate default filename if not provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filter_text = f"_{filter_by}" if filter_by else ""
        filename = f"exchanges{filter_text}_{sort_by}_{timestamp}.json"
    
    # Ensure filename has .json extension
    if not filename.endswith('.json'):
        filename += '.json'
    
    try:
        # Create data object with metadata
        data_object = {
            "generated_at": datetime.now().isoformat(),
            "filter": filter_by,
            "sort_by": sort_by,
            "count": len(exchanges_data),
            "exchanges": exchanges_data
        }
        
        # Write to file
        with open(filename, 'w') as f:
            json.dump(data_object, f, indent=4)
            
        return os.path.abspath(filename)
    
    except Exception as e:
        print_error(f"Failed to save exchanges data: {str(e)}")
        return ""

def save_exchange_details(
    exchange_data: Dict[str, Any],
    filename: Optional[str] = None
) -> str:
    """
    Save detailed exchange data to a JSON file.
    
    Args:
        exchange_data: Dictionary containing exchange details
        filename: Optional filename to save data to
        
    Returns:
        Path to the saved file
    """
    if not exchange_data:
        print_error("No data to save.")
        return ""
    
    # Get exchange ID for filename
    exchange_id = exchange_data.get('id', 'exchange')
    exchange_name = exchange_data.get('name', 'Unknown Exchange')
    
    # Generate default filename if not provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"exchange_{exchange_id}_{timestamp}.json"
    
    # Ensure filename has .json extension
    if not filename.endswith('.json'):
        filename += '.json'
    
    try:
        # Create data object with metadata
        data_object = {
            "generated_at": datetime.now().isoformat(),
            "exchange_id": exchange_id,
            "exchange_name": exchange_name,
            "data": exchange_data
        }
        
        # Write to file
        with open(filename, 'w') as f:
            json.dump(data_object, f, indent=4)
            
        return os.path.abspath(filename)
    
    except Exception as e:
        print_error(f"Failed to save exchange details: {str(e)}")
        return ""

def analyze_exchange_activity(
    exchanges_data: List[Dict[str, Any]],
    top_n: int = 10
) -> None:
    """
    Analyze exchange activity and provide insights.
    
    Args:
        exchanges_data: List of exchanges data
        top_n: Number of top exchanges to analyze
    """
    if not exchanges_data or len(exchanges_data) == 0:
        print_warning("No exchange data available for analysis.")
        return
    
    console.print("\n[bold cyan]📊 Exchange Market Analysis[/bold cyan]\n")
    
    # Calculate total volume
    total_volume = sum(exchange.get('trade_volume_24h_btc', 0) for exchange in exchanges_data)
    
    if total_volume == 0:
        print_warning("No trading volume data available for analysis.")
        return
    
    # Calculate market concentration (% of volume in top exchanges)
    volume_sorted = sorted(exchanges_data, key=lambda x: x.get('trade_volume_24h_btc', 0), reverse=True)
    top_exchanges = volume_sorted[:top_n]
    top_volume = sum(exchange.get('trade_volume_24h_btc', 0) for exchange in top_exchanges)
    top_concentration = (top_volume / total_volume) * 100 if total_volume > 0 else 0
    
    console.print(f"[bold]Top {top_n} Exchanges Market Share:[/bold] {top_concentration:.2f}%")
    
    # Calculate volume distribution
    console.print(f"\n[bold]Volume Distribution:[/bold]")
    for i, exchange in enumerate(top_exchanges[:5], 1):
        name = exchange.get('name', 'Unknown')
        volume = exchange.get('trade_volume_24h_btc', 0)
        share = (volume / total_volume) * 100 if total_volume > 0 else 0
        console.print(f"{i}. {name}: ₿ {volume:,.2f} ({share:.2f}%)")
    
    # Display geographical distribution
    country_volumes = {}
    for exchange in exchanges_data:
        country = exchange.get('country', 'Unknown')
        volume = exchange.get('trade_volume_24h_btc', 0)
        
        if country in country_volumes:
            country_volumes[country] += volume
        else:
            country_volumes[country] = volume
    
    # Sort countries by volume
    countries_sorted = sorted(country_volumes.items(), key=lambda x: x[1], reverse=True)
    top_countries = countries_sorted[:5]
    
    console.print(f"\n[bold]Geographical Distribution (Top 5 Countries):[/bold]")
    for country, volume in top_countries:
        share = (volume / total_volume) * 100 if total_volume > 0 else 0
        console.print(f"{country}: ₿ {volume:,.2f} ({share:.2f}%)")
    
    # Calculate trust score statistics
    trust_scores = [exchange.get('trust_score', 0) for exchange in exchanges_data if exchange.get('trust_score') is not None]
    if trust_scores:
        avg_trust = sum(trust_scores) / len(trust_scores)
        max_trust = max(trust_scores)
        min_trust = min(trust_scores)
        
        console.print(f"\n[bold]Trust Score Statistics:[/bold]")
        console.print(f"Average Trust Score: {avg_trust:.1f}/10")
        console.print(f"Highest Trust Score: {max_trust}/10")
        console.print(f"Lowest Trust Score: {min_trust}/10")
    
    # Age distribution
    years = [exchange.get('year_established', 0) for exchange in exchanges_data 
             if exchange.get('year_established') is not None and exchange.get('year_established') > 0]
    if years:
        current_year = datetime.now().year
        new_exchanges = sum(1 for year in years if year >= current_year - 2)
        established_exchanges = sum(1 for year in years if year <= current_year - 5)
        
        console.print(f"\n[bold]Age Distribution:[/bold]")
        console.print(f"New Exchanges (last 2 years): {new_exchanges} ({new_exchanges/len(years)*100:.1f}%)")
        console.print(f"Established Exchanges (5+ years): {established_exchanges} ({established_exchanges/len(years)*100:.1f}%)")
        
        oldest = min(years) if years else "N/A"
        newest = max(years) if years else "N/A"
        
        console.print(f"Oldest Exchange: {oldest}")
        console.print(f"Newest Exchange: {newest}")
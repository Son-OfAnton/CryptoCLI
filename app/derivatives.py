"""
Module for retrieving and displaying information about derivatives exchanges and tickers.
"""
from typing import Dict, List, Any, Optional, Tuple
import json
import os
from datetime import datetime
import time
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.box import ROUNDED
from rich.progress import Progress, TextColumn, BarColumn, SpinnerColumn, TimeElapsedColumn

from app.api import api
from app.utils.formatting import (
    console,
    print_error,
    print_warning,
    print_success,
    format_currency,
    format_large_number,
    format_price_change
)

def get_derivatives_exchanges(
    limit: int = 50,
    display: bool = True,
    filter_by: Optional[str] = None,
    sort_by: str = "open_interest_btc",
    save: bool = False,
    output: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get a list of derivatives exchanges.
    
    Args:
        limit: Maximum number of exchanges to display (default: 50)
        display: Whether to display the data in the console
        filter_by: Optional filter to search exchange names, IDs, or countries
        sort_by: Field to sort by (open_interest_btc, volume_24h, name)
        save: Whether to save the data to a JSON file
        output: Optional filename to save data to
        
    Returns:
        List of derivatives exchanges data
    """
    try:
        # Show progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Fetching derivatives exchanges data...", total=1)
            
            # Make API request
            response = api._make_request("derivatives/exchanges")
            
            # Complete task
            progress.update(task, completed=1)
            
        if not response:
            print_error("Failed to retrieve derivatives exchanges data.")
            return []
        
        # Extract exchanges data
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
        if sort_by == "open_interest_btc":
            exchanges_data.sort(key=lambda x: float(x.get('open_interest_btc', 0) or 0), reverse=True)
        elif sort_by == "volume_24h":
            exchanges_data.sort(key=lambda x: float(x.get('trade_volume_24h_btc', 0) or 0), reverse=True)
        elif sort_by == "name":
            exchanges_data.sort(key=lambda x: x.get('name', '').lower())
        
        # Apply limit
        exchanges_data = exchanges_data[:limit]
        
        # Display data if requested
        if display:
            display_derivatives_exchanges(exchanges_data, filter_by, sort_by)
        
        # Save data if requested
        if save:
            file_path = save_derivatives_exchanges(exchanges_data, filter_by, sort_by, output)
            print_success(f"Derivatives exchanges data saved to: {file_path}")
        
        return exchanges_data
        
    except Exception as e:
        print_error(f"Error retrieving derivatives exchanges data: {str(e)}")
        return []

def display_derivatives_exchanges(
    exchanges_data: List[Dict[str, Any]],
    filter_by: Optional[str] = None,
    sort_by: str = "open_interest_btc"
) -> None:
    """
    Display derivatives exchanges in a formatted table.
    
    Args:
        exchanges_data: List of derivatives exchanges data
        filter_by: Filter that was applied
        sort_by: Field that was used for sorting
    """
    if not exchanges_data:
        print_warning("No derivatives exchanges found that match the criteria.")
        return
    
    # Create title based on filters and sorting
    title = "📈 Derivatives Exchanges"
    if filter_by:
        title += f" matching '{filter_by}'"
    
    sort_display = {
        "open_interest_btc": "Open Interest (BTC)",
        "volume_24h": "24h Volume",
        "name": "Name"
    }.get(sort_by, sort_by.replace("_", " ").title())
    
    title += f" (Sorted by {sort_display})"
    
    # Create table
    table = Table(title=title, box=ROUNDED)
    
    # Add columns
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Exchange", style="cyan")
    table.add_column("Open Interest (BTC)", justify="right")
    table.add_column("24h Volume (BTC)", justify="right")
    table.add_column("Perpetuals", justify="center")
    table.add_column("Futures", justify="center")
    table.add_column("Number of Coins", justify="center")
    table.add_column("URL", style="blue")
    
    # Add rows
    for i, exchange in enumerate(exchanges_data, 1):
        name = exchange.get('name', 'Unknown')
        
        # Format open interest
        open_interest_btc = exchange.get('open_interest_btc', 0)
        if open_interest_btc is None:
            open_interest_btc = 0
        open_interest_display = f"₿ {float(open_interest_btc):,.2f}" if open_interest_btc else "N/A"
        
        # Format volume
        volume_24h_btc = exchange.get('trade_volume_24h_btc', 0)
        if volume_24h_btc is None:
            volume_24h_btc = 0
        volume_24h_display = f"₿ {float(volume_24h_btc):,.2f}" if volume_24h_btc else "N/A"
        
        # Format perpetuals available
        perpetuals = "Yes" if exchange.get('has_trading_incentive', False) else "No"
        
        # Format futures available
        futures = "Yes" if exchange.get('has_trading_incentive', False) else "No"
        
        # Get number of coins
        num_coins = exchange.get('number_of_coins', 'N/A')
        
        # Format URL
        url = exchange.get('url', '') or "N/A"
        
        table.add_row(
            str(i),
            name,
            open_interest_display,
            volume_24h_display,
            perpetuals,
            futures,
            str(num_coins),
            url
        )
    
    # Display table
    console.print("\n")
    console.print(table)
    
    # Display summary
    console.print(f"\n[bold]Total Derivatives Exchanges:[/bold] {len(exchanges_data)}")
    
    # Calculate totals
    total_open_interest = sum(float(exchange.get('open_interest_btc', 0) or 0) for exchange in exchanges_data)
    total_volume = sum(float(exchange.get('trade_volume_24h_btc', 0) or 0) for exchange in exchanges_data)
    
    console.print(f"[bold]Total Open Interest:[/bold] ₿ {total_open_interest:,.2f}")
    console.print(f"[bold]Total 24h Volume:[/bold] ₿ {total_volume:,.2f}")
    
    # Display timestamp
    console.print(f"\n[dim]Data retrieved at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")

def save_derivatives_exchanges(
    exchanges_data: List[Dict[str, Any]],
    filter_by: Optional[str] = None,
    sort_by: str = "open_interest_btc",
    filename: Optional[str] = None
) -> str:
    """
    Save derivatives exchanges data to a JSON file.
    
    Args:
        exchanges_data: List of derivatives exchanges data
        filter_by: Filter that was applied
        sort_by: Field that was used for sorting
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
        filename = f"derivatives_exchanges{filter_text}_{sort_by}_{timestamp}.json"
    
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
            "total_open_interest_btc": sum(float(exchange.get('open_interest_btc', 0) or 0) for exchange in exchanges_data),
            "total_volume_24h_btc": sum(float(exchange.get('trade_volume_24h_btc', 0) or 0) for exchange in exchanges_data),
            "exchanges": exchanges_data
        }
        
        # Write to file
        with open(filename, 'w') as f:
            json.dump(data_object, f, indent=4)
            
        return os.path.abspath(filename)
    
    except Exception as e:
        print_error(f"Failed to save derivatives exchanges data: {str(e)}")
        return ""

def get_derivatives_exchange_tickers(
    exchange_id: str,
    limit: int = 100,
    display: bool = True,
    filter_by: Optional[str] = None,
    save: bool = False,
    output: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get tickers from a specific derivatives exchange.
    
    Args:
        exchange_id: ID of the derivatives exchange
        limit: Maximum number of tickers to display (default: 100)
        display: Whether to display the data in the console
        filter_by: Optional filter to search by base/target symbol
        save: Whether to save the data to a JSON file
        output: Optional filename to save data to
        
    Returns:
        List of tickers data
    """
    try:
        # Show progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task(f"[cyan]Fetching tickers for {exchange_id}...", total=1)
            
            # Make API request
            endpoint = f"derivatives/exchanges/{exchange_id}/tickers"
            tickers_data = api._make_request(endpoint)
            
            # Complete task
            progress.update(task, completed=1)
            
        if not tickers_data or 'tickers' not in tickers_data:
            print_error(f"Failed to retrieve tickers for derivatives exchange: {exchange_id}")
            return []
        
        # Extract tickers
        tickers = tickers_data.get('tickers', [])
        
        # Apply filter if provided
        if filter_by:
            filtered_tickers = []
            filter_by = filter_by.lower()
            for ticker in tickers:
                base = ticker.get('base', '').lower()
                target = ticker.get('target', '').lower()
                symbol = ticker.get('symbol', '').lower()
                
                if filter_by in base or filter_by in target or filter_by in symbol:
                    filtered_tickers.append(ticker)
                    
            tickers = filtered_tickers
        
        # Sort by volume by default
        tickers.sort(key=lambda x: float(x.get('converted_volume', {}).get('btc', 0) or 0), reverse=True)
        
        # Apply limit
        tickers = tickers[:limit]
        
        # Display data if requested
        if display:
            display_derivatives_tickers(tickers, exchange_id, filter_by)
        
        # Save data if requested
        if save:
            file_path = save_derivatives_tickers(tickers, exchange_id, filter_by, output)
            print_success(f"Derivatives tickers data saved to: {file_path}")
        
        return tickers
        
    except Exception as e:
        print_error(f"Error retrieving derivatives tickers: {str(e)}")
        return []

def get_all_derivatives_tickers(
    limit: int = 100,
    display: bool = True,
    filter_by: Optional[str] = None,
    save: bool = False,
    output: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get tickers from all derivatives exchanges.
    
    Args:
        limit: Maximum number of tickers to display (default: 100)
        display: Whether to display the data in the console
        filter_by: Optional filter to search by base/target symbol or exchange
        save: Whether to save the data to a JSON file
        output: Optional filename to save data to
        
    Returns:
        List of tickers data
    """
    try:
        # Show progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            # First, get the list of derivatives exchanges
            task1 = progress.add_task("[cyan]Fetching derivatives exchanges...", total=1)
            exchanges = api._make_request("derivatives/exchanges")
            progress.update(task1, completed=1)
            
            if not exchanges:
                print_error("Failed to retrieve derivatives exchanges.")
                return []
                
            # Then, get tickers for each exchange
            all_tickers = []
            task2 = progress.add_task("[cyan]Fetching tickers from all exchanges...", total=len(exchanges))
            
            for exchange in exchanges:
                exchange_id = exchange.get('id')
                if not exchange_id:
                    progress.update(task2, advance=1)
                    continue
                
                try:
                    endpoint = f"derivatives/exchanges/{exchange_id}/tickers"
                    exchange_tickers = api._make_request(endpoint)
                    
                    if exchange_tickers and 'tickers' in exchange_tickers:
                        # Add exchange information to each ticker
                        for ticker in exchange_tickers['tickers']:
                            ticker['exchange_id'] = exchange_id
                            ticker['exchange_name'] = exchange.get('name', 'Unknown')
                            all_tickers.append(ticker)
                except Exception as e:
                    # If we can't get tickers for this exchange, continue to the next one
                    pass
                
                progress.update(task2, advance=1)
        
        if not all_tickers:
            print_error("No tickers found from derivatives exchanges.")
            return []
        
        # Apply filter if provided
        if filter_by:
            filtered_tickers = []
            filter_by = filter_by.lower()
            for ticker in all_tickers:
                base = ticker.get('base', '').lower()
                target = ticker.get('target', '').lower()
                symbol = ticker.get('symbol', '').lower()
                exchange_id = ticker.get('exchange_id', '').lower()
                exchange_name = ticker.get('exchange_name', '').lower()
                
                if (filter_by in base or filter_by in target or filter_by in symbol or
                    filter_by in exchange_id or filter_by in exchange_name):
                    filtered_tickers.append(ticker)
                    
            all_tickers = filtered_tickers
        
        # Sort by volume by default
        all_tickers.sort(key=lambda x: float(x.get('converted_volume', {}).get('btc', 0) or 0), reverse=True)
        
        # Apply limit
        all_tickers = all_tickers[:limit]
        
        # Display data if requested
        if display:
            display_all_derivatives_tickers(all_tickers, filter_by)
        
        # Save data if requested
        if save:
            file_path = save_all_derivatives_tickers(all_tickers, filter_by, output)
            print_success(f"All derivatives tickers data saved to: {file_path}")
        
        return all_tickers
        
    except Exception as e:
        print_error(f"Error retrieving all derivatives tickers: {str(e)}")
        return []

def display_derivatives_tickers(
    tickers: List[Dict[str, Any]],
    exchange_id: str,
    filter_by: Optional[str] = None
) -> None:
    """
    Display tickers from a derivatives exchange in a formatted table.
    
    Args:
        tickers: List of tickers data
        exchange_id: ID of the derivatives exchange
        filter_by: Filter that was applied
    """
    if not tickers:
        print_warning(f"No tickers found for {exchange_id} that match the criteria.")
        return
    
    # Create title
    title = f"📊 Derivatives Tickers - {exchange_id.capitalize()}"
    if filter_by:
        title += f" (Filtered by '{filter_by}')"
    
    # Create table
    table = Table(title=title, box=ROUNDED)
    
    # Add columns
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Symbol", style="cyan")
    table.add_column("Base/Target", style="blue")
    table.add_column("Price (USD)", justify="right")
    table.add_column("Price (BTC)", justify="right")
    table.add_column("Volume (USD)", justify="right")
    table.add_column("Volume (BTC)", justify="right")
    table.add_column("Open Interest (USD)", justify="right")
    table.add_column("Contract Type", justify="center")
    
    # Add rows
    for i, ticker in enumerate(tickers, 1):
        # Extract data
        symbol = ticker.get('symbol', 'Unknown')
        base = ticker.get('base', '')
        target = ticker.get('target', '')
        base_target = f"{base}/{target}" if base and target else "N/A"
        
        # Format prices
        price_usd = ticker.get('converted_last', {}).get('usd', 0)
        price_btc = ticker.get('converted_last', {}).get('btc', 0)
        
        price_usd_display = f"${float(price_usd):,.8f}" if price_usd else "N/A"
        price_btc_display = f"₿ {float(price_btc):.8f}" if price_btc else "N/A"
        
        # Format volumes
        volume_usd = ticker.get('converted_volume', {}).get('usd', 0)
        volume_btc = ticker.get('converted_volume', {}).get('btc', 0)
        
        volume_usd_display = f"${float(volume_usd):,.2f}" if volume_usd else "N/A"
        volume_btc_display = f"₿ {float(volume_btc):.2f}" if volume_btc else "N/A"
        
        # Format open interest
        open_interest_usd = ticker.get('open_interest_usd', 0)
        open_interest_display = f"${float(open_interest_usd):,.2f}" if open_interest_usd else "N/A"
        
        # Contract type
        contract_type = ticker.get('contract_type', 'N/A')
        
        table.add_row(
            str(i),
            symbol,
            base_target,
            price_usd_display,
            price_btc_display,
            volume_usd_display,
            volume_btc_display,
            open_interest_display,
            contract_type
        )
    
    # Display table
    console.print("\n")
    console.print(table)
    
    # Display summary
    console.print(f"\n[bold]Total Tickers:[/bold] {len(tickers)}")
    
    # Calculate totals
    total_volume_usd = sum(float(ticker.get('converted_volume', {}).get('usd', 0) or 0) for ticker in tickers)
    total_volume_btc = sum(float(ticker.get('converted_volume', {}).get('btc', 0) or 0) for ticker in tickers)
    total_open_interest = sum(float(ticker.get('open_interest_usd', 0) or 0) for ticker in tickers)
    
    console.print(f"[bold]Total Volume (USD):[/bold] ${total_volume_usd:,.2f}")
    console.print(f"[bold]Total Volume (BTC):[/bold] ₿ {total_volume_btc:,.2f}")
    console.print(f"[bold]Total Open Interest (USD):[/bold] ${total_open_interest:,.2f}")
    
    # Display timestamp
    console.print(f"\n[dim]Data retrieved at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")

def display_all_derivatives_tickers(
    tickers: List[Dict[str, Any]],
    filter_by: Optional[str] = None
) -> None:
    """
    Display tickers from all derivatives exchanges in a formatted table.
    
    Args:
        tickers: List of tickers data from all exchanges
        filter_by: Filter that was applied
    """
    if not tickers:
        print_warning("No derivatives tickers found that match the criteria.")
        return
    
    # Create title
    title = "📊 Derivatives Tickers - All Exchanges"
    if filter_by:
        title += f" (Filtered by '{filter_by}')"
    
    # Create table
    table = Table(title=title, box=ROUNDED)
    
    # Add columns
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Exchange", style="green")
    table.add_column("Symbol", style="cyan")
    table.add_column("Base/Target", style="blue")
    table.add_column("Price (USD)", justify="right")
    table.add_column("Volume (USD)", justify="right")
    table.add_column("Open Interest (USD)", justify="right")
    table.add_column("Contract Type", justify="center")
    
    # Add rows
    for i, ticker in enumerate(tickers, 1):
        # Extract data
        exchange_name = ticker.get('exchange_name', 'Unknown')
        symbol = ticker.get('symbol', 'Unknown')
        base = ticker.get('base', '')
        target = ticker.get('target', '')
        base_target = f"{base}/{target}" if base and target else "N/A"
        
        # Format price
        price_usd = ticker.get('converted_last', {}).get('usd', 0)
        price_usd_display = f"${float(price_usd):,.8f}" if price_usd else "N/A"
        
        # Format volume
        volume_usd = ticker.get('converted_volume', {}).get('usd', 0)
        volume_usd_display = f"${float(volume_usd):,.2f}" if volume_usd else "N/A"
        
        # Format open interest
        open_interest_usd = ticker.get('open_interest_usd', 0)
        open_interest_display = f"${float(open_interest_usd):,.2f}" if open_interest_usd else "N/A"
        
        # Contract type
        contract_type = ticker.get('contract_type', 'N/A')
        
        table.add_row(
            str(i),
            exchange_name,
            symbol,
            base_target,
            price_usd_display,
            volume_usd_display,
            open_interest_display,
            contract_type
        )
    
    # Display table
    console.print("\n")
    console.print(table)
    
    # Display summary
    console.print(f"\n[bold]Total Tickers:[/bold] {len(tickers)}")
    
    # Count unique exchanges
    unique_exchanges = set(ticker.get('exchange_id', '') for ticker in tickers)
    console.print(f"[bold]Exchanges Represented:[/bold] {len(unique_exchanges)}")
    
    # Calculate totals
    total_volume_usd = sum(float(ticker.get('converted_volume', {}).get('usd', 0) or 0) for ticker in tickers)
    total_open_interest = sum(float(ticker.get('open_interest_usd', 0) or 0) for ticker in tickers)
    
    console.print(f"[bold]Total Volume (USD):[/bold] ${total_volume_usd:,.2f}")
    console.print(f"[bold]Total Open Interest (USD):[/bold] ${total_open_interest:,.2f}")
    
    # Count contract types
    contract_types = {}
    for ticker in tickers:
        contract_type = ticker.get('contract_type', 'Unknown')
        if contract_type in contract_types:
            contract_types[contract_type] += 1
        else:
            contract_types[contract_type] = 1
    
    console.print("\n[bold]Contract Types:[/bold]")
    for contract_type, count in sorted(contract_types.items(), key=lambda x: x[1], reverse=True):
        console.print(f"{contract_type}: {count} ({count/len(tickers)*100:.1f}%)")
    
    # Display timestamp
    console.print(f"\n[dim]Data retrieved at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")

def save_derivatives_tickers(
    tickers: List[Dict[str, Any]],
    exchange_id: str,
    filter_by: Optional[str] = None,
    filename: Optional[str] = None
) -> str:
    """
    Save derivatives tickers data to a JSON file.
    
    Args:
        tickers: List of tickers data
        exchange_id: ID of the derivatives exchange
        filter_by: Filter that was applied
        filename: Optional filename to save data to
        
    Returns:
        Path to the saved file
    """
    if not tickers:
        print_error("No data to save.")
        return ""
    
    # Generate default filename if not provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filter_text = f"_{filter_by}" if filter_by else ""
        filename = f"derivatives_tickers_{exchange_id}{filter_text}_{timestamp}.json"
    
    # Ensure filename has .json extension
    if not filename.endswith('.json'):
        filename += '.json'
    
    try:
        # Calculate totals for metadata
        total_volume_usd = sum(float(ticker.get('converted_volume', {}).get('usd', 0) or 0) for ticker in tickers)
        total_volume_btc = sum(float(ticker.get('converted_volume', {}).get('btc', 0) or 0) for ticker in tickers)
        total_open_interest = sum(float(ticker.get('open_interest_usd', 0) or 0) for ticker in tickers)
        
        # Create data object with metadata
        data_object = {
            "generated_at": datetime.now().isoformat(),
            "exchange_id": exchange_id,
            "filter": filter_by,
            "count": len(tickers),
            "total_volume_usd": total_volume_usd,
            "total_volume_btc": total_volume_btc,
            "total_open_interest_usd": total_open_interest,
            "tickers": tickers
        }
        
        # Write to file
        with open(filename, 'w') as f:
            json.dump(data_object, f, indent=4)
            
        return os.path.abspath(filename)
    
    except Exception as e:
        print_error(f"Failed to save derivatives tickers data: {str(e)}")
        return ""

def save_all_derivatives_tickers(
    tickers: List[Dict[str, Any]],
    filter_by: Optional[str] = None,
    filename: Optional[str] = None
) -> str:
    """
    Save all derivatives tickers data to a JSON file.
    
    Args:
        tickers: List of tickers data from all exchanges
        filter_by: Filter that was applied
        filename: Optional filename to save data to
        
    Returns:
        Path to the saved file
    """
    if not tickers:
        print_error("No data to save.")
        return ""
    
    # Generate default filename if not provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filter_text = f"_{filter_by}" if filter_by else ""
        filename = f"all_derivatives_tickers{filter_text}_{timestamp}.json"
    
    # Ensure filename has .json extension
    if not filename.endswith('.json'):
        filename += '.json'
    
    try:
        # Calculate totals for metadata
        total_volume_usd = sum(float(ticker.get('converted_volume', {}).get('usd', 0) or 0) for ticker in tickers)
        total_volume_btc = sum(float(ticker.get('converted_volume', {}).get('btc', 0) or 0) for ticker in tickers)
        total_open_interest = sum(float(ticker.get('open_interest_usd', 0) or 0) for ticker in tickers)
        
        # Count unique exchanges
        unique_exchanges = set(ticker.get('exchange_id', '') for ticker in tickers)
        
        # Create data object with metadata
        data_object = {
            "generated_at": datetime.now().isoformat(),
            "filter": filter_by,
            "count": len(tickers),
            "unique_exchanges": len(unique_exchanges),
            "total_volume_usd": total_volume_usd,
            "total_volume_btc": total_volume_btc,
            "total_open_interest_usd": total_open_interest,
            "tickers": tickers
        }
        
        # Write to file
        with open(filename, 'w') as f:
            json.dump(data_object, f, indent=4)
            
        return os.path.abspath(filename)
    
    except Exception as e:
        print_error(f"Failed to save all derivatives tickers data: {str(e)}")
        return ""
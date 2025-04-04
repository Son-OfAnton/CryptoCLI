"""
Functionality for retrieving and displaying public companies' cryptocurrency holdings.
"""
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import os
from decimal import Decimal

from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from app.api import api
from app.utils.formatting import (
    console, 
    print_error, 
    print_warning,
    format_currency, 
    format_large_number,
    format_percentage
)

def get_companies_treasury(coin_id: str, display=True, save=False, output=None):
    """
    Get and optionally display public companies holding a specific cryptocurrency.
    
    Args:
        coin_id: ID of the coin (e.g., "bitcoin" or "ethereum")
        display: Whether to display the data in the console
        save: Whether to save the data to a file
        output: Filename to save data to (if save is True)
        
    Returns:
        dict: Companies treasury data or None if an error occurs
    """
    try:
        # Get companies treasury data from API
        treasury_data = api.get_companies_public_treasury(coin_id)
        
        # Check if we have a valid response
        if not treasury_data:
            print_error(f"Failed to get companies treasury data for {coin_id} from CoinGecko API.")
            return None
        
        # Display the data if requested
        if display:
            display_companies_treasury(treasury_data, coin_id)
        
        # Save the data if requested
        if save:
            file_path = save_companies_treasury(treasury_data, coin_id, output)
            console.print(f"\n[green]Companies treasury data saved to:[/green] {file_path}")
        
        return treasury_data
    
    except Exception as e:
        print_error(f"Error retrieving companies treasury data: {str(e)}")
        return None

def display_companies_treasury(data: Dict[str, Any], coin_id: str):
    """
    Display public companies' cryptocurrency holdings in a formatted table.
    
    Args:
        data: Treasury data from the API
        coin_id: ID of the cryptocurrency
    """
    # Get the companies list
    companies = data.get("companies", [])
    
    if not companies:
        print_warning(f"No public companies found holding {coin_id}.")
        return
    
    # Get total holdings and statistics
    total_holdings = data.get("total_holdings", 0)
    total_value_usd = data.get("total_value_usd", 0)
    market_cap_dominance = data.get("market_cap_dominance", 0)
    
    # Create a header with summary information
    coin_name = coin_id.title()  # Capitalize first letter
    header_text = Text()
    header_text.append(f"\n[bold]Public Companies Holding {coin_name}[/bold]\n\n")
    
    header_text.append("🏢 [bold]Total Companies:[/bold] ")
    header_text.append(f"{len(companies)}\n")
    
    header_text.append("💰 [bold]Total Holdings:[/bold] ")
    header_text.append(f"{format_large_number(total_holdings)} {coin_id.upper()}")
    header_text.append(f" ({format_currency(total_value_usd, 'USD')})\n")
    
    header_text.append("📊 [bold]Market Cap Dominance:[/bold] ")
    header_text.append(f"{format_percentage(market_cap_dominance)}\n")
    
    header_panel = Panel(
        header_text,
        title=f"[bold cyan]Companies' {coin_name} Treasury Holdings[/bold cyan]",
        border_style="cyan"
    )
    console.print(header_panel)
    
    # Create a table for the companies
    table = Table(title=f"Public Companies with {coin_name} on Balance Sheet")
    
    # Define table columns
    table.add_column("Rank", style="dim", justify="right")
    table.add_column("Company", style="cyan")
    table.add_column("Country", style="blue")
    table.add_column(f"{coin_id.upper()} Holdings", justify="right")
    table.add_column("Entry Value (USD)", justify="right")
    table.add_column("Current Value (USD)", justify="right")
    table.add_column("% of Total Supply", justify="right")
    
    # Add rows to the table
    for i, company in enumerate(companies, 1):
        name = company.get("name", "Unknown")
        country = company.get("country", "")
        
        # Format the holdings
        holdings = company.get("total_holdings", 0)
        holdings_formatted = format_large_number(holdings)
        
        # Format the entry value
        entry_value_usd = company.get("total_entry_value_usd", 0)
        entry_value_formatted = format_currency(entry_value_usd, "USD")
        
        # Format the current value
        current_value_usd = company.get("total_current_value_usd", 0)
        current_value_formatted = format_currency(current_value_usd, "USD")
        
        # Calculate and format percentage of total supply
        percentage_of_total = company.get("percentage_of_total_supply", 0)
        percentage_formatted = format_percentage(percentage_of_total)
        
        table.add_row(
            str(i),
            name,
            country,
            holdings_formatted,
            entry_value_formatted,
            current_value_formatted,
            percentage_formatted
        )
    
    console.print("\n")
    console.print(table)

def save_companies_treasury(data: Dict[str, Any], coin_id: str, filename: Optional[str] = None) -> str:
    """
    Save companies' treasury data to a JSON file.
    
    Args:
        data: Companies treasury data
        coin_id: ID of the cryptocurrency
        filename: Optional filename to save data to
        
    Returns:
        str: Path to the saved file
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"companies_{coin_id}_treasury_{timestamp}.json"
    
    # Ensure the filename has a .json extension
    if not filename.endswith('.json'):
        filename += '.json'
    
    # Write data to file
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    
    return os.path.abspath(filename)
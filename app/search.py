"""
Module for searching cryptocurrencies by name or symbol.
"""
from typing import Dict, List, Any, Optional
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .api import api
from .utils.formatting import (
    console,
    print_error,
    print_warning,
    print_success
)

def search_cryptocurrencies(query: str, limit: int = 10, display: bool = True) -> Dict[str, Any]:
    """
    Search for cryptocurrencies by name or symbol.
    
    Args:
        query: Search query (name or symbol)
        limit: Maximum number of results to return (default: 10)
        display: Whether to display the results
        
    Returns:
        Dictionary containing search results
    """
    try:
        # Make API request to search for cryptocurrencies
        search_results = api.search_coins(query)
        
        # Extract coin data from the response
        all_coins = search_results.get('coins', [])
        
        # Limit the results if needed
        limited_results = all_coins[:limit] if limit > 0 else all_coins
        
        # Display the results if requested
        if display and limited_results:
            display_search_results(limited_results)
        elif display:
            print_warning(f"No cryptocurrencies found matching '{query}'")
        
        # Return the search results (with or without limiting)
        return {
            'query': query,
            'total_results': len(all_coins),
            'displayed_results': len(limited_results),
            'coins': limited_results
        }
    except Exception as e:
        print_error(f"Failed to search for cryptocurrencies: {str(e)}")
        return {
            'query': query,
            'total_results': 0,
            'displayed_results': 0,
            'coins': []
        }

def display_search_results(coins: List[Dict[str, Any]]) -> None:
    """
    Display cryptocurrency search results in a table.
    
    Args:
        coins: List of coin data from search results
    """
    if not coins:
        print_warning("No search results to display.")
        return
    
    # Create a table for displaying search results
    table = Table(title="Cryptocurrency Search Results")
    
    # Add columns for the table
    table.add_column("Rank", style="dim", justify="right")
    table.add_column("ID", style="cyan", justify="left")
    table.add_column("Name", style="bright_white", justify="left")
    table.add_column("Symbol", style="green", justify="left")
    table.add_column("Market Cap Rank", justify="right")
    
    # Add rows for each coin
    for i, coin in enumerate(coins, 1):
        market_cap_rank = coin.get('market_cap_rank')
        market_cap_display = f"#{market_cap_rank}" if market_cap_rank else "N/A"
        
        table.add_row(
            str(i),
            coin.get('id', 'N/A'),
            coin.get('name', 'N/A'),
            coin.get('symbol', 'N/A').upper(),
            market_cap_display
        )
    
    # Display the table
    console.print(table)
    
    # Print a note about how to use the results
    console.print("\n[dim]Note: Use the ID in the second column with other commands. For example:[/dim]")
    example_id = coins[0].get('id', 'bitcoin') if coins else 'bitcoin'
    console.print(f"[yellow]CryptoCLI price {example_id}[/yellow] - to get the current price")
    console.print(f"[yellow]CryptoCLI history {example_id} --period week[/yellow] - to get historical data")

def get_cryptocurrency_suggestion(partial_name: str) -> Optional[str]:
    """
    Search for a cryptocurrency by partial name and return the best match.
    Useful for command auto-completion or suggestions.
    
    Args:
        partial_name: Partial cryptocurrency name or symbol
        
    Returns:
        Best matching cryptocurrency ID or None if no matches found
    """
    try:
        # Search for cryptocurrencies matching the partial name
        search_results = search_cryptocurrencies(partial_name, limit=1, display=False)
        
        # Extract the best match
        coins = search_results.get('coins', [])
        if coins:
            return coins[0].get('id')
        
        return None
    except Exception:
        return None
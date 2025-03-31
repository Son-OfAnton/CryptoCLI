"""
Main CLI entry point for the crypto-stats application.
"""
import click
from rich.console import Console
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from .api import api
from .price import get_current_prices, get_prices_with_change
from .utils.formatting import (
    console,
    print_error,
    print_success,
    print_warning
)

DEFAULT_CURRENCY = "usd"
DEFAULT_LIMIT = 10

@click.group()
def cli():
    """Cryptocurrency statistics from the CoinGecko API."""
    pass

@cli.command()
@click.argument('coin_ids', nargs=-1)
@click.option('--currencies', '-c', default='usd',
              help='Comma-separated list of currencies (e.g., usd,eur,btc)')
@click.option('--detailed', '-d', is_flag=True,
              help='Show more detailed information including 24h change')
def price(coin_ids, currencies, detailed):
    """Get current prices for specific coins."""
    if not coin_ids:
        print_error("Please specify at least one coin ID")
        return
        
    currencies_list = currencies.split(',')
    
    if detailed and len(currencies_list) == 1:
        # If detailed view is requested and only one currency, use markets endpoint
        get_prices_with_change(list(coin_ids), currencies_list[0])
    else:
        # Otherwise use simple price endpoint
        get_current_prices(list(coin_ids), currencies_list)

@cli.command()
def config():
    """
    Display current configuration.
    """
    console.print("[bold]CryptoStats CLI Configuration[/bold]\n")
    
    # Show API configuration
    console.print("[cyan]API Configuration:[/cyan]")
    api_url = os.getenv("COINGECKO_BASE_URL", "https://api.coingecko.com/api/v3")
    console.print(f"API URL: {api_url}")
    
    # Show if API key is set
    api_key = os.getenv("COINGECKO_API_KEY")
    if api_key:
        console.print("API Key: [green]Set[/green]")
    else:
        console.print("API Key: [red]Not set[/red] (using free tier or mock mode)")
    
    # Show mock mode status
    mock_mode = os.getenv("CRYPTO_STATS_MOCK", "false").lower() == "true" or not api_key
    console.print(f"Mock Mode: {'[yellow]Enabled[/yellow]' if mock_mode else '[green]Disabled[/green]'}")
    
    # Show rate limiting info
    console.print(f"\nRate Limiting: ~{api.rate_limit_wait:.1f} seconds between requests")

if __name__ == '__main__':
    cli()
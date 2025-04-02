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
from .history import get_historical_prices, DAY, WEEK, MONTH, YEAR, save_historical_data
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

@cli.command()
@click.argument('coin_id')
@click.option('--currency', '-c', default='usd',
              help='Currency to get data in (e.g., usd, eur)')
@click.option('--period', '-p', type=click.Choice(['day', 'week', 'month', 'year', 'custom']),
              default='week', help='Time period for historical data')
@click.option('--days', '-d', type=int, default=None,
              help='Custom number of days (for custom period)')
@click.option('--save', '-s', is_flag=True,
              help='Save historical data to a JSON file')
@click.option('--output', '-o', type=str, default=None,
              help='Filename to save data to (requires --save)')
def history(coin_id, currency, period, days, save, output):
    """Get historical price data for a specific coin."""
    # Determine the number of days based on period
    if period == 'day':
        days_to_fetch = DAY
    elif period == 'week':
        days_to_fetch = WEEK
    elif period == 'month':
        days_to_fetch = MONTH
    elif period == 'year':
        days_to_fetch = YEAR
    elif period == 'custom':
        if days is None:
            print_error("For custom period, you must specify the number of days using --days")
            return
        days_to_fetch = days
    else:
        days_to_fetch = WEEK  # Default
    
    # Get historical data
    historical_data = get_historical_prices(
        coin_id=coin_id,
        vs_currency=currency,
        days=days_to_fetch
    )
    
    # Save historical data if requested
    if save and historical_data:
        save_historical_data(historical_data, output)

if __name__ == '__main__':
    cli()
"""
Main CLI entry point for the crypto-stats application.
"""
import click
from rich.console import Console
import sys

from .api import api
from .price import get_current_prices, get_prices_with_change
from .utils.formatting import (
    console,
    create_coin_list_table,
    create_coin_detail_panel,
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

if __name__ == '__main__':
    cli()

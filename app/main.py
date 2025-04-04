"""
Main CLI entry point for the crypto-stats application.
"""
from app.currencies import get_supported_currencies
from app.defi_data import get_defi_data
from app.global_data import get_global_data
from app.ohlc import get_ohlc_data, save_ohlc_data
from app.trending import get_trending_coins
from app.utils.formatting import (
    console,
    print_error,
    print_success,
    print_warning
)
from app.search import search_cryptocurrencies
from app.history import get_historical_prices, DAY, WEEK, MONTH, YEAR, save_historical_data
from app.price import get_current_prices, get_prices_with_change
from app.api import api
import click
from rich.console import Console
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


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
    api_url = os.getenv("COINGECKO_BASE_URL",
                        "https://api.coingecko.com/api/v3")
    console.print(f"API URL: {api_url}")

    # Show if API key is set
    api_key = os.getenv("COINGECKO_API_KEY")
    if api_key:
        console.print("API Key: [green]Set[/green]")
    else:
        console.print(
            "API Key: [red]Not set[/red] (using free tier or mock mode)")

    # Show mock mode status
    mock_mode = os.getenv("CRYPTO_STATS_MOCK",
                          "false").lower() == "true" or not api_key
    console.print(
        f"Mock Mode: {'[yellow]Enabled[/yellow]' if mock_mode else '[green]Disabled[/green]'}")

    # Show rate limiting info
    console.print(
        f"\nRate Limiting: ~{api.rate_limit_wait:.1f} seconds between requests")


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
            print_error(
                "For custom period, you must specify the number of days using --days")
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


@cli.command()
@click.argument('query')
@click.option('--limit', '-l', type=int, default=10,
              help='Maximum number of results to display (default: 10)')
def search(query, limit):
    """
    Search for cryptocurrencies by name or symbol.

    Examples:
        CryptoCLI search bitcoin
        CryptoCLI search eth
        CryptoCLI search dog --limit 5
    """
    if not query:
        print_error("Please provide a search query")
        return

    # Search for cryptocurrencies
    search_cryptocurrencies(query, limit=limit)


@cli.command()
@click.argument('coin_id')
@click.option('--currency', '-c', default='usd',
              help='Currency to get data in (e.g., usd, eur)')
@click.option('--days', '-d', type=click.Choice(['1', '7', '14', '30', '90', '180', '365']),
              default='7', help='Number of days of data to return')
@click.option('--save', '-s', is_flag=True,
              help='Save OHLC data to a JSON file')
@click.option('--output', '-o', type=str, default=None,
              help='Filename to save data to (requires --save)')
def ohlc(coin_id, currency, days, save, output):
    """
    Get OHLC (Open, High, Low, Close) chart data for a specific coin.

    Examples:
        CryptoCLI ohlc bitcoin
        CryptoCLI ohlc ethereum --currency eur
        CryptoCLI ohlc solana --days 30
        CryptoCLI ohlc cardano --days 90 --save
    """
    # Convert days to integer
    days_int = int(days)

    # Get OHLC data
    ohlc_data = get_ohlc_data(
        coin_id=coin_id,
        vs_currency=currency,
        days=days_int
    )

    # Save OHLC data if requested
    if save and ohlc_data:
        save_ohlc_data(ohlc_data, coin_id, currency, days_int, output)


@cli.command()
@click.argument('contract_address')
@click.option('--platform', '-p', default='ethereum',
              help='Asset platform (ethereum, binance-smart-chain, polygon-pos, etc.)')
@click.option('--currency', '-c', default='usd',
              help='Currency to display market data in (e.g., usd, eur)')
@click.option('--tickers/--no-tickers', default=True,
              help='Display exchange ticker information')
@click.option('--tickers-limit', '-t', type=int, default=5,
              help='Maximum number of exchange tickers to display')
@click.option('--save', '-s', is_flag=True,
              help='Save token data to a JSON file')
@click.option('--output', '-o', type=str, default=None,
              help='Filename to save data to (requires --save)')
def token(contract_address, platform, currency, tickers, tickers_limit, save, output):
    """
    Get detailed data for a token by contract address.

    Examples:
        CryptoCLI token 0x1f9840a85d5af5bf1d1762f925bdaddc4201f984
        CryptoCLI token 0x1f9840a85d5af5bf1d1762f925bdaddc4201f984 --platform ethereum
        CryptoCLI token 0x3ee2200efb3400fabb9aacf31297cbdd1d435d47 --platform binance-smart-chain
        CryptoCLI token 0x1f9840a85d5af5bf1d1762f925bdaddc4201f984 --currency eur
        CryptoCLI token 0x1f9840a85d5af5bf1d1762f925bdaddc4201f984 --no-tickers
        CryptoCLI token 0x1f9840a85d5af5bf1d1762f925bdaddc4201f984 --save
    """
    # Get token data by contract address
    from app.token_metadata import get_token_by_contract, display_token_exchange_tickers, save_token_data

    # Validate contract address format
    if not contract_address.startswith('0x') or len(contract_address) != 42:
        print_error("Invalid contract address. Must be in the format: 0x...")
        return

    # Get token data
    token_data = get_token_by_contract(
        contract_address=contract_address,
        asset_platform=platform,
        vs_currency=currency
    )

    # Display exchange tickers if requested
    if token_data and tickers:
        display_token_exchange_tickers(token_data, tickers_limit)

    # Save token data if requested
    if token_data and save:
        save_token_data(token_data, output)


@cli.command()
@click.option('--format', '-f', type=click.Choice(['table', 'list']), default='table',
              help='Output format (table or list)')
@click.option('--query', '-q', type=str, default=None,
              help='Filter platforms by name or ID')
@click.option('--save', '-s', is_flag=True,
              help='Save platforms data to a JSON file')
@click.option('--output', '-o', type=str, default=None,
              help='Filename to save data to (requires --save)')
def platforms(format, query, save, output):
    """
    List all asset platforms (blockchains) supported by CoinGecko.

    Examples:
        CryptoCLI platforms
        CryptoCLI platforms --format list
        CryptoCLI platforms --query ethereum
        CryptoCLI platforms --save
        CryptoCLI platforms --save --output platforms.json
    """
    from app.platforms import get_asset_platforms, save_platforms_data

    # Get asset platforms
    platforms_data = get_asset_platforms(
        display=True,
        format_type=format,
        query=query
    )

    # Save platforms data if requested
    if platforms_data and save:
        save_platforms_data(platforms_data, output)


@cli.command()
@click.option('--save', '-s', is_flag=True,
              help='Save list of supported currencies to a JSON file')
@click.option('--output', '-o', type=str, default=None,
              help='Filename to save currencies to (requires --save)')
def currencies(save, output):
    """
    List all supported fiat currencies for price conversions.

    Examples:
        CryptoCLI currencies
        CryptoCLI currencies --save
        CryptoCLI currencies --save --output currencies.json
    """
    get_supported_currencies(
        display=True,
        save=save,
        output=output
    )


@cli.command()
@click.option('--save', '-s', is_flag=True,
              help='Save global market data to a JSON file')
@click.option('--output', '-o', type=str, default=None,
              help='Filename to save data to (requires --save)')
def global_data(save, output):
    """
    Show global cryptocurrency market data.

    Displays total market capitalization, trading volume, market dominance,
    and other key statistics about the overall cryptocurrency market.

    Examples:
        CryptoCLI global-data
        CryptoCLI global-data --save
        CryptoCLI global-data --save --output global_market.json
    """
    get_global_data(
        display=True,
        save=save,
        output=output
    )


@cli.command()
@click.option("--save", "-s", is_flag=True,
              help="Save DeFi market data to a JSON file")
@click.option("--output", "-o", type=str, default=None,
              help="Filename to save data to (requires --save)")
@click.option("--top", "-t", type=click.IntRange(1, 100), default=10,
              help="Number of top DeFi tokens to display (1-100)")
def defi(save, output, top):
    """
    Display global DeFi market statistics.

    Shows current DeFi market capitalization, dominance, trading volume,
    and top DeFi tokens by market cap.
    """
    get_defi_data(display=True, save=save, output=output, top_tokens=top)

@cli.command()
@click.option("--save", "-s", is_flag=True,
              help="Save trending coins data to a JSON file")
@click.option("--output", "-o", type=str, default=None,
              help="Filename to save data to (requires --save)")
def trending(save, output):
    """
    Show trending coins on CoinGecko in the last 24 hours.
    
    Displays top coins by interest based on CoinGecko's search and trends data.
    """
    get_trending_coins(display=True, save=save, output=output)


if __name__ == '__main__':
    cli()

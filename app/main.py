"""
Main CLI entry point for the crypto-stats application.
"""
from app.companies import get_companies_treasury
from app.currencies import get_supported_currencies
from app.defi_data import get_defi_data
from app.global_data import get_global_data
from app.ohlc import get_ohlc_data, save_ohlc_data
from app.ohlc_range import get_ohlc_range_data, save_ohlc_range_data
from app.trending import get_trending_coins, get_trending, get_trending_nfts
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
from app.api_usage import get_api_usage, display_usage_stats, save_api_usage_export
from app.gainers_losers import get_gainers_losers, TimePeriod
from app.newly_listed import get_newly_listed_coins, display_new_coin_details, get_detailed_analysis
import click
from rich.console import Console
from rich.table import Table
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
@click.option("--type", "-t", type=click.Choice(["coins", "nfts", "all"]), default="coins",
              help="Type of trending data to display (coins, nfts, or all)")
@click.option("--save", "-s", is_flag=True,
              help="Save trending data to a JSON file")
@click.option("--output", "-o", type=str, default=None,
              help="Filename to save data to (requires --save)")
def trending(type, save, output):
    """
    Show trending coins or NFTs on CoinGecko in the last 24 hours.

    Displays top assets by interest based on CoinGecko's search and trends data.
    """
    get_trending(data_type=type, display=True, save=save, output=output)


@cli.command()
@click.option("--save", "-s", is_flag=True,
              help="Save trending coins data to a JSON file")
@click.option("--output", "-o", type=str, default=None,
              help="Filename to save data to (requires --save)")
def trending_coins(save, output):
    """
    Show trending coins on CoinGecko in the last 24 hours.

    Displays top coins by interest based on CoinGecko's search and trends data.
    """
    get_trending_coins(display=True, save=save, output=output)


@cli.command()
@click.option("--save", "-s", is_flag=True,
              help="Save trending NFTs data to a JSON file")
@click.option("--output", "-o", type=str, default=None,
              help="Filename to save data to (requires --save)")
def trending_nfts(save, output):
    """
    Show trending NFTs on CoinGecko in the last 24 hours.

    Displays top NFT collections by interest based on CoinGecko's search and trends data.
    """
    get_trending_nfts(display=True, save=save, output=output)


@cli.command()
@click.argument('coin_id', type=click.Choice(['bitcoin', 'ethereum']), required=True)
@click.option("--save", "-s", is_flag=True,
              help="Save companies treasury data to a JSON file")
@click.option("--output", "-o", type=str, default=None,
              help="Filename to save data to (requires --save)")
def companies(coin_id, save, output):
    """
    Show public companies holding Bitcoin or Ethereum in their treasury.

    Displays company information, holdings amount, and value statistics.
    """
    get_companies_treasury(coin_id=coin_id, display=True,
                           save=save, output=output)


@cli.command()
@click.option("--refresh", "-r", is_flag=True,
              help="Make a lightweight API call to refresh usage statistics")
@click.option("--save", "-s", is_flag=True,
              help="Save usage statistics to a JSON file")
@click.option("--output", "-o", type=str, default=None,
              help="Filename to save data to (requires --save)")
def usage(refresh, save, output):
    """
    Display CoinGecko API usage statistics.

    Shows rate limits, remaining credits, usage patterns, and provides recommendations
    based on your usage patterns.

    Examples:
        CryptoCLI usage
        CryptoCLI usage --refresh
        CryptoCLI usage --save
        CryptoCLI usage --save --output api_usage.json
    """
    # Get API usage data with optional refresh
    usage_data = get_api_usage(force_refresh=refresh)

    # Display the usage statistics
    display_usage_stats(usage_data)

    # Save usage data if requested
    if save:
        file_path = save_api_usage_export(usage_data, output)
        print_success(f"API usage data saved to: {file_path}")


@cli.command()
@click.option("--period", "-p",
              type=click.Choice(
                  ["1h", "24h", "7d", "14d", "30d", "200d", "1y"]),
              default="24h",
              help="Time period for price change")
@click.option("--currency", "-c", default="usd",
              help="Currency to display prices in (e.g., usd, eur)")
@click.option("--limit", "-l", default=30,
              help="Number of gainers and losers to display")
@click.option("--save", "-s", is_flag=True,
              help="Save gainers and losers data to a JSON file")
@click.option("--output", "-o", type=str, default=None,
              help="Filename to save data to (requires --save)")
def movers(period, currency, limit, save, output):
    """
    Show top cryptocurrency gainers and losers by price change percentage.

    Displays cryptocurrencies with the largest price gains and losses 
    for a specific time period (1h, 24h, 7d, 14d, 30d, 200d, 1y).

    Examples:
        CryptoCLI movers
        CryptoCLI movers --period 7d
        CryptoCLI movers --period 1h --currency eur
        CryptoCLI movers --period 30d --limit 20
        CryptoCLI movers --save
        CryptoCLI movers --save --output price_movers.json
    """
    # Convert limit to integer
    limit = int(limit)

    # Get gainers and losers data
    get_gainers_losers(
        time_period=period,
        vs_currency=currency,
        limit=limit,
        display=True,
        save=save,
        output=output
    )


@cli.command()
@click.option("--days", "-d", type=click.Choice(["7", "14", "30", "all"]),
              default="14",
              help="Show coins listed within this many days (all = no filtering)")
@click.option("--currency", "-c", default="usd",
              help="Currency to display prices in (e.g., usd, eur)")
@click.option("--limit", "-l", default=100, type=int,
              help="Maximum number of newly listed coins to display (up to 250)")
@click.option("--analyze", "-a", is_flag=True,
              help="Show detailed statistical analysis of newly listed coins")
@click.option("--save", "-s", is_flag=True,
              help="Save newly listed coins data to a JSON file")
@click.option("--output", "-o", type=str, default=None,
              help="Filename to save data to (requires --save)")
def new_coins(days, currency, limit, analyze, save, output):
    """
    Show recently listed coins on CoinGecko.

    Displays the most recently listed cryptocurrencies on CoinGecko,
    with options to filter by listing date, limit the number of results,
    and perform statistical analysis.

    Examples:
        CryptoCLI new-coins
        CryptoCLI new-coins --days 7
        CryptoCLI new-coins --days all
        CryptoCLI new-coins --currency eur
        CryptoCLI new-coins --limit 200
        CryptoCLI new-coins --analyze
        CryptoCLI new-coins --save
        CryptoCLI new-coins --save --output new_listings.json
    """
    # Handle the "all" case
    days_filter = 0 if days == "all" else int(days)

    # Get newly listed coins data
    newly_listed = get_newly_listed_coins(
        vs_currency=currency,
        days=days_filter,
        limit=limit,
        display=True,
        save=save,
        output=output
    )

    # Show detailed analysis if requested
    if analyze and newly_listed:
        get_detailed_analysis(newly_listed, currency)


@cli.command()
@click.argument('coin_id')
@click.option("--currency", "-c", default="usd",
              help="Currency to display prices in (e.g., usd, eur)")
def new_coin_details(coin_id, currency):
    """
    Show detailed information about a specific newly listed coin.

    Displays comprehensive details for a specific coin by its CoinGecko ID.
    Use this command to explore a particular newly listed coin in more depth.

    Examples:
        CryptoCLI new-coin-details bitcoin
        CryptoCLI new-coin-details ethereum --currency eur
    """
    try:
        # Get coin data from the new coins endpoint
        new_coins = api._make_request("coins/list/new")

        # Check if the specified coin is in the new coins list
        coin_basic_info = next(
            (coin for coin in new_coins if coin['id'] == coin_id), None)

        if not coin_basic_info:
            print_warning(
                f"Coin with ID '{coin_id}' not found in newly listed coins. Fetching general coin data...")

        # Even if not a newly listed coin, fetch its market data
        params = {
            "vs_currency": currency,
            "ids": coin_id,
            "sparkline": "false",
            "price_change_percentage": "24h,7d"
        }

        # Make the API request to get detailed data
        coin_data = api._make_request("coins/markets", params)

        if not coin_data or len(coin_data) == 0:
            print_error(f"No data found for coin ID: {coin_id}")
            return

        # Combine the data
        combined_data = {**coin_data[0]}
        if coin_basic_info:
            # Add date_added if the coin is in the new coins list
            combined_data['date_added'] = coin_basic_info.get('date_added')

        # Display detailed information about the coin
        display_new_coin_details(combined_data, currency)

    except Exception as e:
        print_error(f"Error retrieving coin details: {str(e)}")


@cli.command()
@click.argument('coin_id')
@click.option('--currency', '-c', default='usd',
              help='Currency to get data in (e.g., usd, eur)')
@click.option('--from-date', '-f', required=True,
              help='Start date in YYYY-MM-DD format (e.g., 2023-01-01)')
@click.option('--to-date', '-t', required=True,
              help='End date in YYYY-MM-DD format (e.g., 2023-03-31)')
@click.option('--save', '-s', is_flag=True,
              help='Save OHLC data to a JSON file')
@click.option('--output', '-o', type=str, default=None,
              help='Filename to save data to (requires --save)')
def ohlc_range(coin_id, currency, from_date, to_date, save, output):
    """
    Get OHLC (Open, High, Low, Close) chart data for a specific coin within a date range.

    Retrieves OHLC data for a cryptocurrency between two specific dates and displays
    the results in a table format with summary statistics and a simple ASCII chart.

    Examples:
        CryptoCLI ohlc-range bitcoin --from-date 2023-01-01 --to-date 2023-03-31
        CryptoCLI ohlc-range ethereum --currency eur --from-date 2023-01-01 --to-date 2023-03-31
        CryptoCLI ohlc-range bitcoin --from-date 2023-01-01 --to-date 2023-03-31 --save
        CryptoCLI ohlc-range bitcoin --from-date 2023-01-01 --to-date 2023-03-31 --save --output bitcoin_q1_2023.json
    """
    from app.ohlc_range import get_ohlc_range_data, save_ohlc_range_data
    from datetime import datetime
    import time

    try:
        # Convert date strings to timestamps
        try:
            from_timestamp = int(datetime.strptime(
                from_date, "%Y-%m-%d").timestamp())
            to_timestamp = int(datetime.strptime(
                to_date, "%Y-%m-%d").timestamp())

            # Add 1 day to to_timestamp to include the end date
            to_timestamp += 24 * 60 * 60  # Add 1 day in seconds
        except ValueError:
            print_error(
                "Invalid date format. Please use YYYY-MM-DD format (e.g., 2023-01-01)")
            return

        # Get OHLC data
        ohlc_data = get_ohlc_range_data(
            coin_id=coin_id,
            vs_currency=currency,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            display=True
        )

        # Save OHLC data if requested
        if save and ohlc_data:
            save_ohlc_range_data(
                ohlc_data=ohlc_data,
                coin_id=coin_id,
                vs_currency=currency,
                from_timestamp=from_timestamp,
                to_timestamp=to_timestamp,
                filename=output
            )

    except Exception as e:
        print_error(f"Error retrieving OHLC range data: {str(e)}")


@cli.command()
@click.argument('coin_id')
@click.option('--days', '-d', default=30, type=int,
              help='Number of days of historical data to retrieve (default: 30)')
@click.option('--analyze', '-a', is_flag=True,
              help='Perform detailed trend analysis of the supply data')
@click.option('--save', '-s', is_flag=True,
              help='Save supply history data to a JSON file')
@click.option('--output', '-o', type=str, default=None,
              help='Filename to save data to (requires --save)')
def supply_history(coin_id, days, analyze, save, output):
    """
    Get historical circulating supply data for a specific coin.

    Retrieves and displays estimated circulating supply history for a cryptocurrency
    over a specified number of days, with options to analyze supply trends and save data.

    Examples:
        CryptoCLI supply-history bitcoin
        CryptoCLI supply-history ethereum --days 90
        CryptoCLI supply-history bitcoin --days 365 --analyze
        CryptoCLI supply-history bitcoin --save
        CryptoCLI supply-history bitcoin --save --output bitcoin_supply.json
    """
    from app.supply_history import get_supply_history, analyze_supply_trends

    # Get the supply history data
    supply_data = get_supply_history(
        coin_id=coin_id,
        days=days,
        display=True,
        save=save,
        output=output
    )

    # Perform trend analysis if requested
    if analyze and supply_data:
        analyze_supply_trends(supply_data, coin_id)


@cli.command()
@click.option("--limit", "-l", default=100, type=int,
              help="Maximum number of exchanges to display (default: 100)")
@click.option("--filter", "-f", type=str, default=None,
              help="Filter exchanges by name, ID, or country")
@click.option("--sort", "-s", type=click.Choice(["trust_score", "volume_24h", "name", "country"]),
              default="trust_score", help="Sort exchanges by field")
@click.option("--analyze", "-a", is_flag=True,
              help="Perform analysis on exchange market data")
@click.option("--save", "-v", is_flag=True,
              help="Save exchanges data to a JSON file")
@click.option("--output", "-o", type=str, default=None,
              help="Filename to save data to (requires --save)")
def exchanges(limit, filter, sort, analyze, save, output):
    """
    List cryptocurrency exchanges with active trading volumes.

    Retrieves and displays data about cryptocurrency exchanges including
    name, country, trust score, and 24-hour trading volume.

    Examples:
        CryptoCLI exchanges
        CryptoCLI exchanges --limit 50
        CryptoCLI exchanges --filter binance
        CryptoCLI exchanges --filter US
        CryptoCLI exchanges --sort volume_24h
        CryptoCLI exchanges --analyze
        CryptoCLI exchanges --save
        CryptoCLI exchanges --save --output exchanges_data.json
    """
    from app.exchanges import get_exchanges, analyze_exchange_activity

    # Get exchanges data
    exchanges_data = get_exchanges(
        limit=limit,
        display=True,
        filter_by=filter,
        sort_by=sort,
        save=save,
        output=output
    )

    # Perform analysis if requested
    if analyze and exchanges_data:
        analyze_exchange_activity(exchanges_data)


@cli.command()
@click.argument('exchange_id')
@click.option("--save", "-s", is_flag=True,
              help="Save exchange details to a JSON file")
@click.option("--output", "-o", type=str, default=None,
              help="Filename to save data to (requires --save)")
def exchange_details(exchange_id, save, output):
    """
    Get detailed information about a specific cryptocurrency exchange.

    Retrieves and displays comprehensive details about a specific exchange,
    including trading pairs, volume, social media links, and status updates.

    Examples:
        CryptoCLI exchange-details binance
        CryptoCLI exchange-details coinbase
        CryptoCLI exchange-details kraken --save
        CryptoCLI exchange-details ftx --save --output ftx_details.json
    """
    from app.exchanges import get_exchange_details

    # Get exchange details
    get_exchange_details(
        exchange_id=exchange_id,
        display=True,
        save=save,
        output=output
    )


@cli.command()
@click.argument('exchange_id')
@click.option('--from-date', '-f', type=str, required=True,
              help='Start date in YYYY-MM-DD format')
@click.option('--to-date', '-t', type=str, required=True,
              help='End date in YYYY-MM-DD format')
@click.option('--from-timestamp', type=int, 
              help='Start date as UNIX timestamp (overrides --from-date if provided)')
@click.option('--to-timestamp', type=int,
              help='End date as UNIX timestamp (overrides --to-date if provided)')
@click.option('--save', '-s', is_flag=True,
              help='Save volume data to a JSON file (default)')
@click.option('--format', '-f', type=click.Choice(['json', 'csv', 'both']),
              default='json', help='Output file format(s)')
@click.option('--output', '-o', type=str, default=None,
              help='Filename to save data to (without extension, requires --save)')
@click.option('--output-dir', '-d', type=str, default=None,
              help='Directory to save output files (requires --save)')
@click.option('--analyze', '-a', is_flag=True,
              help='Perform additional analysis on volume trends')
@click.option('--export-all', '-e', is_flag=True,
              help='Export to JSON, CSV, and create a summary report')
def exchange_volume(exchange_id, from_date, to_date, from_timestamp, to_timestamp, 
                   save, format, output, output_dir, analyze, export_all):
    """
    Get historical trading volume data in BTC for a specific exchange within a date range.
    
    Examples:
        CryptoCLI exchange-volume binance --from-date 2023-01-01 --to-date 2023-01-31
        CryptoCLI exchange-volume coinbase_pro --from-timestamp 1672531200 --to-timestamp 1675209600
        CryptoCLI exchange-volume kraken --from-date 2023-01-01 --to-date 2023-01-31 --save
        CryptoCLI exchange-volume binance --from-date 2023-01-01 --to-date 2023-01-31 --analyze
        CryptoCLI exchange-volume binance --from-date 2023-01-01 --to-date 2023-01-31 --format csv
        CryptoCLI exchange-volume binance --from-date 2023-01-01 --to-date 2023-01-31 --export-all
    """
    from app.exchange_volume import (
        get_exchange_volume_history, 
        save_exchange_volume_data,
        convert_date_to_timestamp,
        analyze_volume_trends,
        export_volume_data_summary
    )
    
    # Convert date strings to timestamps if needed
    if from_timestamp is None:
        from_timestamp = convert_date_to_timestamp(from_date)
    
    if to_timestamp is None:
        to_timestamp = convert_date_to_timestamp(to_date)
    
    # Validate timestamps
    if from_timestamp <= 0 or to_timestamp <= 0:
        print_error("Invalid date format or timestamps.")
        return
    
    if from_timestamp >= to_timestamp:
        print_error("From date must be earlier than to date.")
        return
    
    # Get volume data
    volume_data = get_exchange_volume_history(
        exchange_id=exchange_id,
        from_timestamp=from_timestamp,
        to_timestamp=to_timestamp,
        display=True
    )
    
    # Perform analysis if requested
    if analyze and volume_data and volume_data.get("success", False):
        analysis = analyze_volume_trends(volume_data)
        
        if "error" not in analysis:
            # Add analysis to volume data for export
            volume_data["trend_analysis"] = analysis
            
            # Display trend information
            console.print("\n[bold cyan]Volume Trend Analysis[/bold cyan]")
            
            # Show trend direction with color
            trend = analysis.get("trend_direction", "unknown")
            if trend == "increasing":
                trend_str = "[bold green]Increasing[/bold green]"
            elif trend == "decreasing":
                trend_str = "[bold red]Decreasing[/bold red]"
            else:
                trend_str = "[bold yellow]Stable[/bold yellow]"
                
            console.print(f"Overall Trend: {trend_str}")
            console.print(f"Volume Volatility: {analysis.get('volatility', 0):.2f}%")
            console.print(f"Average Daily Change: {analysis.get('mean_daily_change', 0):.2f}%")
            
            # Display day of week analysis
            day_analysis = analysis.get("day_of_week_analysis", {})
            
            # Create a table for day of week analysis
            day_table = Table(title="Volume by Day of Week")
            day_table.add_column("Day", style="cyan")
            day_table.add_column("Avg. Volume (BTC)", justify="right")
            day_table.add_column("Relative to Average", justify="right")
            
            if day_analysis and "average_volumes" in day_analysis:
                day_volumes = day_analysis["average_volumes"]
                all_avg = sum(day_volumes.values()) / 7 if day_volumes else 0
                
                for day, volume in day_volumes.items():
                    rel_to_avg = (volume / all_avg * 100) - 100 if all_avg > 0 else 0
                    rel_style = "green" if rel_to_avg > 0 else "red" if rel_to_avg < 0 else "white"
                    rel_sign = "+" if rel_to_avg > 0 else ""
                    
                    day_table.add_row(
                        day,
                        f"{volume:,.2f}",
                        f"[{rel_style}]{rel_sign}{rel_to_avg:.2f}%[/{rel_style}]"
                    )
                
                console.print(day_table)
                
                # Print highest and lowest volume days
                console.print(f"Highest Volume: [green]{day_analysis.get('highest_volume_day', 'Unknown')}[/green]")
                console.print(f"Lowest Volume: [red]{day_analysis.get('lowest_volume_day', 'Unknown')}[/red]")
        else:
            print_warning(f"Could not perform analysis: {analysis.get('error')}")
    
    # Save data if requested
    if save and volume_data and volume_data.get("success", False):
        if export_all:
            # Export to all formats with summary
            json_path, csv_path, summary_path = export_volume_data_summary(
                volume_data, 
                output_dir=output_dir
            )
            if json_path and csv_path and summary_path:
                console.print("\n[bold green]Data exported successfully:[/bold green]")
                console.print(f"JSON: {json_path}")
                console.print(f"CSV: {csv_path}")
                console.print(f"Summary: {summary_path}")
        else:
            # Export to single format
            if format == 'both':
                # Save as both JSON and CSV
                json_output = output + '.json' if output else None
                csv_output = output + '.csv' if output else None
                
                # If output directory is specified, join with filenames
                if output_dir:
                    if json_output:
                        json_output = os.path.join(output_dir, json_output)
                    if csv_output:
                        csv_output = os.path.join(output_dir, csv_output)
                
                json_path = save_exchange_volume_data(volume_data, json_output, 'json')
                csv_path = save_exchange_volume_data(volume_data, csv_output, 'csv')
                
                if json_path and csv_path:
                    console.print("\n[bold green]Data saved to:[/bold green]")
                    console.print(f"JSON: {json_path}")
                    console.print(f"CSV: {csv_path}")
            else:
                # Save in the specified format
                if output_dir and output:
                    full_output = os.path.join(output_dir, output)
                elif output_dir:
                    full_output = output_dir  # Will generate default filename
                else:
                    full_output = output
                
                save_exchange_volume_data(volume_data, full_output, format)
    """
    Get historical trading volume data for a specific exchange.

    Retrieves and displays historical trading volume in BTC for a specific exchange
    over a specified number of days, with options to analyze volume patterns and save data.

    Examples:
        CryptoCLI exchange-volume binance
        CryptoCLI exchange-volume coinbase --days 90
        CryptoCLI exchange-volume kraken --days 365 --analyze
        CryptoCLI exchange-volume binance --save
        CryptoCLI exchange-volume ftx --save --output ftx_volume.json
    """
    from app.exchange_volume import get_exchange_volume_history, analyze_volume_patterns

    # Get the exchange volume history data
    volume_data = get_exchange_volume_history(
        exchange_id=exchange_id,
        display=True,
        save=save,
        output=output
    )

    # Perform pattern analysis if requested
    if analyze and volume_data:
        analyze_volume_patterns(volume_data, exchange_id)


@cli.command()
@click.option('--limit', '-l', default=50, type=int,
              help='Maximum number of exchanges to display (default: 50)')
@click.option('--filter', '-f', type=str, default=None,
              help='Filter exchanges by name, ID, or country')
@click.option('--sort', '-s', type=click.Choice(['open_interest_btc', 'volume_24h', 'name']),
              default='open_interest_btc', help='Sort exchanges by field')
@click.option('--save', '-v', is_flag=True,
              help='Save derivatives exchanges data to a JSON file')
@click.option('--output', '-o', type=str, default=None,
              help='Filename to save data to (requires --save)')
def derivatives_exchanges(limit, filter, sort, save, output):
    """
    List derivatives exchanges with active trading.

    Retrieves and displays data about cryptocurrency derivatives exchanges
    including open interest, trading volume, and number of supported assets.

    Examples:
        CryptoCLI derivatives-exchanges
        CryptoCLI derivatives-exchanges --limit 20
        CryptoCLI derivatives-exchanges --filter binance
        CryptoCLI derivatives-exchanges --sort volume_24h
        CryptoCLI derivatives-exchanges --save
        CryptoCLI derivatives-exchanges --save --output derivatives_data.json
    """
    from app.derivatives import get_derivatives_exchanges

    # Get derivatives exchanges data
    get_derivatives_exchanges(
        limit=limit,
        display=True,
        filter_by=filter,
        sort_by=sort,
        save=save,
        output=output
    )


@cli.command()
@click.argument('exchange_id', required=True)
@click.option('--limit', '-l', default=100, type=int,
              help='Maximum number of tickers to display (default: 100)')
@click.option('--filter', '-f', type=str, default=None,
              help='Filter tickers by base/target symbol')
@click.option('--save', '-s', is_flag=True,
              help='Save derivatives tickers data to a JSON file')
@click.option('--output', '-o', type=str, default=None,
              help='Filename to save data to (requires --save)')
def derivatives_tickers(exchange_id, limit, filter, save, output):
    """
    Get tickers from a specific derivatives exchange.

    Retrieves and displays all derivatives contracts (tickers) from a specific
    derivatives exchange, including price, volume, and open interest data.

    Examples:
        CryptoCLI derivatives-tickers binance
        CryptoCLI derivatives-tickers bitmex --limit 50
        CryptoCLI derivatives-tickers deribit --filter btc
        CryptoCLI derivatives-tickers bybit --save
        CryptoCLI derivatives-tickers ftx --save --output ftx_futures.json
    """
    from app.derivatives import get_derivatives_exchange_tickers

    # Get derivatives tickers data
    get_derivatives_exchange_tickers(
        exchange_id=exchange_id,
        limit=limit,
        display=True,
        filter_by=filter,
        save=save,
        output=output
    )


@cli.command()
@click.option('--limit', '-l', default=100, type=int,
              help='Maximum number of tickers to display (default: 100)')
@click.option('--filter', '-f', type=str, default=None,
              help='Filter tickers by symbol or exchange')
@click.option('--save', '-s', is_flag=True,
              help='Save all derivatives tickers data to a JSON file')
@click.option('--output', '-o', type=str, default=None,
              help='Filename to save data to (requires --save)')
def all_derivatives_tickers(limit, filter, save, output):
    """
    Get tickers from all derivatives exchanges.

    Retrieves and displays derivatives contracts (tickers) from all derivatives
    exchanges, aggregating them into a single view and sorted by trading volume.

    Examples:
        CryptoCLI all-derivatives-tickers
        CryptoCLI all-derivatives-tickers --limit 50
        CryptoCLI all-derivatives-tickers --filter btc
        CryptoCLI all-derivatives-tickers --filter binance
        CryptoCLI all-derivatives-tickers --save
        CryptoCLI all-derivatives-tickers --save --output all_futures.json
    """
    from app.derivatives import get_all_derivatives_tickers

    # Get all derivatives tickers data
    get_all_derivatives_tickers(
        limit=limit,
        display=True,
        filter_by=filter,
        save=save,
        output=output
    )


@cli.command()
@click.option('--limit', '-l', type=int, default=100,
              help='Number of collections to display (max 250)')
@click.option('--currency', '-c', default='usd',
              help='Currency to display prices in (e.g., usd, eth)')
@click.option('--order', '-o',
              type=click.Choice([
                  'h24_volume_native_desc', 'h24_volume_native_asc',
                  'floor_price_native_desc', 'floor_price_native_asc',
                  'market_cap_native_desc', 'market_cap_native_asc',
                  'market_cap_usd_desc', 'market_cap_usd_asc'
              ]),
              default='h24_volume_native_desc',
              help='Sort order for collections')
@click.option('--save', '-s', is_flag=True,
              help='Save collections data to a JSON file')
@click.option('--output', '-o', type=str, default=None,
              help='Filename to save data to (requires --save)')
def nft_collections(limit, currency, order, save, output):
    """
    List NFT collections with market data.

    Displays NFT collections with their floor prices, market caps, volumes, and price changes.

    Examples:
        CryptoCLI nft-collections
        CryptoCLI nft-collections --limit 50
        CryptoCLI nft-collections --order floor_price_native_desc
        CryptoCLI nft-collections --currency eth
        CryptoCLI nft-collections --save --output nft_data.json
    """
    from app.nft_collections import get_nft_collections, save_nft_collections_data

    # Get NFT collections data
    collections_data = get_nft_collections(
        limit=limit,
        vs_currency=currency,
        order=order,
        display=True
    )

    # Save data if requested
    if save and collections_data and collections_data.get("collections"):
        save_nft_collections_data(collections_data, output)


@cli.command()
@click.argument('collection_id')
@click.option('--currency', '-c', default='usd',
              help='Currency to display prices in (e.g., usd, eth)')
@click.option('--save', '-s', is_flag=True,
              help='Save collection details to a JSON file')
@click.option('--output', '-o', type=str, default=None,
              help='Filename to save data to (requires --save)')
def nft_collection(collection_id, currency, save, output):
    """
    Get detailed information about a specific NFT collection.

    Displays detailed data for a single NFT collection including market data, price history,
    statistics, and external links.

    Examples:
        CryptoCLI nft-collection cryptopunks
        CryptoCLI nft-collection bored-ape-yacht-club --currency eth
        CryptoCLI nft-collection doodles-official --save
    """
    from app.nft_collections import get_nft_collection_by_id, save_nft_collection_details

    # Get NFT collection details
    collection_data = get_nft_collection_by_id(
        collection_id=collection_id,
        vs_currency=currency,
        display=True
    )

    # Save data if requested
    if save and collection_data and collection_data.get("success", False):
        save_nft_collection_details(collection_data, output)


@cli.command()
@click.argument('collection_id')
@click.option('--days', '-d', type=int, default=30,
              help='Number of days of historical data (max 365)')
@click.option('--currency', '-c', default='usd',
              help='Currency to display prices in (e.g., usd, eth)')
@click.option('--save', '-s', is_flag=True,
              help='Save historical data to a JSON file')
@click.option('--output', '-o', type=str, default=None,
              help='Filename to save data to (requires --save)')
def nft_history(collection_id, days, currency, save, output):
    """
    Get historical market data for an NFT collection.

    Displays floor price, market cap, and 24h volume history for a specific NFT collection
    over a specified number of days.

    Examples:
        CryptoCLI nft-history bored-ape-yacht-club
        CryptoCLI nft-history cryptopunks --days 90
        CryptoCLI nft-history doodles-official --currency eth
        CryptoCLI nft-history azuki --days 180 --save
    """
    from app.nft_collections import get_nft_collection_historical_data, save_nft_historical_data

    # Get historical data
    historical_data = get_nft_collection_historical_data(
        collection_id=collection_id,
        days=days,
        vs_currency=currency,
        display=True
    )

    # Save data if requested
    if save and historical_data and historical_data.get("success", False):
        save_nft_historical_data(historical_data, output)


@cli.command()
@click.argument('contract_address')
@click.option('--platform', '-p', default='ethereum',
              type=click.Choice(['ethereum', 'solana', 'polygon-pos', 'arbitrum-one',
                                'optimistic-ethereum', 'binance-smart-chain', 'fantom', 'avalanche']),
              help='Blockchain platform the NFT is deployed on')
@click.option('--days', '-d', type=int, default=30,
              help='Number of days of historical data (max 365)')
@click.option('--currency', '-c', default='usd',
              help='Currency to display prices in (e.g., usd, eth)')
@click.option('--save', '-s', is_flag=True,
              help='Save historical data to a JSON file')
@click.option('--output', '-o', type=str, default=None,
              help='Filename to save data to (requires --save)')
def nft_contract_history(contract_address, platform, days, currency, save, output):
    """
    Get historical market data for an NFT collection by contract address.

    Displays floor price, market cap, and 24h volume history for an NFT collection
    identified by its contract address, over a specified number of days.

    Examples:
        CryptoCLI nft-contract-history 0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d
        CryptoCLI nft-contract-history 0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d --days 90
        CryptoCLI nft-contract-history 0x8a90cab2b38dba80c64b7734e58ee1db38b8992e --platform ethereum --currency eth
        CryptoCLI nft-contract-history 0xed5af388653567af2f388e6224dc7c4b3241c544 --days 180 --save
    """
    from app.nft_collections import get_nft_historical_data_by_contract, save_nft_historical_data

    # Get historical data by contract address
    historical_data = get_nft_historical_data_by_contract(
        contract_address=contract_address,
        days=days,
        asset_platform=platform,
        vs_currency=currency,
        display=True
    )

    # Save data if requested
    if save and historical_data and historical_data.get("success", False):
        save_nft_historical_data(historical_data, output)


@cli.command()
@click.argument('collection_id')
@click.option('--currency', '-c', default='usd',
              help='Currency to display prices in (e.g., usd, eth)')
@click.option('--save', '-s', is_flag=True,
              help='Save marketplace data to a JSON file')
@click.option('--output', '-o', type=str, default=None,
              help='Filename to save data to (requires --save)')
def nft_marketplaces(collection_id, currency, save, output):
    """
    Get marketplace data for an NFT collection by collection ID.

    Displays floor price and volume data across different NFT marketplaces
    for a specific collection.

    Examples:
        CryptoCLI nft-marketplaces bored-ape-yacht-club
        CryptoCLI nft-marketplaces cryptopunks --currency eth
        CryptoCLI nft-marketplaces doodles-official --save
    """
    from app.nft_marketplaces import get_nft_marketplace_data, save_nft_marketplace_data

    # Get marketplace data
    marketplace_data = get_nft_marketplace_data(
        collection_identifier=collection_id,
        vs_currency=currency,
        is_contract_address=False,
        display=True
    )

    # Save data if requested
    if save and marketplace_data and marketplace_data.get("success", False):
        save_nft_marketplace_data(marketplace_data, output)


@cli.command()
@click.argument('contract_address')
@click.option('--platform', '-p', default='ethereum',
              type=click.Choice(['ethereum', 'solana', 'polygon-pos', 'arbitrum-one',
                                'optimistic-ethereum', 'binance-smart-chain', 'fantom', 'avalanche']),
              help='Blockchain platform the NFT is deployed on')
@click.option('--currency', '-c', default='usd',
              help='Currency to display prices in (e.g., usd, eth)')
@click.option('--save', '-s', is_flag=True,
              help='Save marketplace data to a JSON file')
@click.option('--output', '-o', type=str, default=None,
              help='Filename to save data to (requires --save)')
def nft_contract_marketplaces(contract_address, platform, currency, save, output):
    """
    Get marketplace data for an NFT collection by contract address.

    Displays floor price and volume data across different NFT marketplaces
    for a specific collection identified by its contract address.

    Examples:
        CryptoCLI nft-contract-marketplaces 0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d
        CryptoCLI nft-contract-marketplaces 0x8a90cab2b38dba80c64b7734e58ee1db38b8992e --currency eth
        CryptoCLI nft-contract-marketplaces 0xed5af388653567af2f388e6224dc7c4b3241c544 --save
    """
    from app.nft_marketplaces import get_nft_marketplace_data, save_nft_marketplace_data

    # Get marketplace data by contract address
    marketplace_data = get_nft_marketplace_data(
        collection_identifier=contract_address,
        vs_currency=currency,
        is_contract_address=True,
        asset_platform=platform,
        display=True
    )

    # Save data if requested
    if save and marketplace_data and marketplace_data.get("success", False):
        save_nft_marketplace_data(marketplace_data, output)


if __name__ == '__main__':
    cli()

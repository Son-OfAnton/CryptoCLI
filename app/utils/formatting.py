"""
Formatting utilities for the CLI interface.
"""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from typing import Dict, List, Any, Tuple
import datetime

console = Console()


def format_price_change(change: float) -> Text:
    """Format price change with color based on positive or negative value."""
    text = f"{change:.2f}%"
    if change > 0:
        return Text(text, style="green")
    elif change < 0:
        return Text(text, style="red")
    return Text(text)


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format amount as currency."""
    if currency.lower() == "usd":
        return f"${amount:,.2f}"
    elif currency.lower() == "eur":
        return f"€{amount:,.2f}"
    elif currency.lower() == "gbp":
        return f"£{amount:,.2f}"
    elif currency.lower() == "jpy":
        return f"¥{amount:,.0f}"
    else:
        return f"{amount:,.2f} {currency.upper()}"


def format_large_number(number: float) -> str:
    """Format large numbers with K, M, B, T suffixes."""
    if number is None:
        return "N/A"

    if abs(number) >= 1_000_000_000_000:
        return f"{number/1_000_000_000_000:.2f}T"
    elif abs(number) >= 1_000_000_000:
        return f"{number/1_000_000_000:.2f}B"
    elif abs(number) >= 1_000_000:
        return f"{number/1_000_000:.2f}M"
    elif abs(number) >= 1_000:
        return f"{number/1_000:.2f}K"
    return f"{number:.2f}"


def format_timestamp(timestamp: int) -> str:
    """Format unix timestamp to human-readable date."""
    if timestamp is None:
        return "N/A"
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


def create_coin_list_table(coins: List[Dict[str, Any]], currency: str = "usd") -> Table:
    """Create a rich table for displaying a list of coins."""
    table = Table(title=f"Top Cryptocurrencies (in {currency.upper()})")

    table.add_column("#", justify="right")
    table.add_column("Coin", justify="left")
    table.add_column("Price", justify="right")
    table.add_column("24h %", justify="right")
    table.add_column("7d %", justify="right")
    table.add_column("Market Cap", justify="right")
    table.add_column("Volume (24h)", justify="right")

    for i, coin in enumerate(coins, 1):
        table.add_row(
            str(i),
            f"{coin['name']} ({coin['symbol'].upper()})",
            format_currency(coin['current_price'], currency),
            format_price_change(coin.get('price_change_percentage_24h', 0)),
            format_price_change(
                coin.get('price_change_percentage_7d_in_currency', 0)),
            format_large_number(coin['market_cap']),
            format_large_number(coin['total_volume'])
        )

    return table


def create_coin_detail_panel(coin: Dict[str, Any], currency: str = "usd") -> Panel:
    """Create a rich panel for displaying detailed coin information."""
    currency = currency.lower()

    content = Text()
    content.append(f"Rank: #{coin.get('market_cap_rank', 'N/A')}\n\n")

    content.append("Price: ")
    content.append(
        f"{format_currency(coin['market_data']['current_price'][currency], currency)}\n"
    )

    content.append("24h Change: ")
    content.append(
        format_price_change(coin['market_data'].get(
            'price_change_percentage_24h', 0))
    )
    content.append("\n")

    content.append("Market Cap: ")
    content.append(
        f"{format_large_number(coin['market_data']['market_cap'][currency])}\n"
    )

    content.append("24h Volume: ")
    content.append(
        f"{format_large_number(coin['market_data']['total_volume'][currency])}\n"
    )

    content.append("Circulating Supply: ")
    content.append(
        f"{format_large_number(coin['market_data'].get('circulating_supply', 0))}\n"
    )

    if coin['market_data'].get('max_supply'):
        content.append("Max Supply: ")
        content.append(
            f"{format_large_number(coin['market_data']['max_supply'])}\n")

    content.append("\nDescription:\n")
    description = coin.get('description', {}).get(
        'en', 'No description available')
    # Truncate long descriptions
    if len(description) > 300:
        description = description[:300] + "..."
    content.append(description)

    return Panel(
        content,
        title=f"{coin['name']} ({coin['symbol'].upper()})",
        subtitle=f"Last updated: {format_timestamp(coin['last_updated'])}"
    )


def print_error(message: str):
    """Print an error message."""
    console.print(f"[bold red]Error:[/bold red] {message}")


def print_warning(message: str):
    """Print a warning message."""
    console.print(f"[bold yellow]Warning:[/bold yellow] {message}")


def print_success(message: str):
    """Print a success message."""
    console.print(f"[bold green]Success:[/bold green] {message}")


def format_percentage(value: float, decimal_places: int = 2) -> str:
    """
    Format a float value as a percentage string.

    Args:
        value: Float value to format (0.01 = 1%)
        decimal_places: Number of decimal places to show

    Returns:
        Formatted percentage string
    """
    if value is None:
        return "N/A"

    try:
        # Convert to float if it might be a string
        value = float(value)

        # Format as percentage with specified decimal places
        return f"{value:.{decimal_places}f}%"
    except ValueError:
        return "N/A"

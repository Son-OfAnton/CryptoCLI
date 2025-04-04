# CryptoCLI

A powerful command-line tool for viewing cryptocurrency statistics from CoinGecko.

![CryptoCLI Screenshot](https://example.com/screenshot.png) <!-- Placeholder for screenshot -->

## Overview

CryptoCLI provides a comprehensive interface to cryptocurrency data, allowing you to quickly access prices, historical data, OHLC charts, and search for cryptocurrencies—all directly from your terminal.

## Features

- **Real-time Price Data**: Get current prices for cryptocurrencies in multiple fiat currencies
- **Detailed Market Data**: View comprehensive market information including price changes, volume, and market cap
- **Historical Price Data**: Access historical price information with customizable time periods
- **OHLC Chart Data**: Analyze Open, High, Low, Close price patterns with ASCII visualization
- **Cryptocurrency Search**: Find cryptocurrencies by name or symbol
- **Multiple Output Formats**: View data in tables, charts, and export to JSON
- **Configuration Management**: View and manage API connection settings

## Installation

### Prerequisites

- Python 3.6+
- pip (Python package manager)

### Install from PyPI

```bash
pip install CryptoCLI
```

### Install from Source

```bash
# Clone the repository
git clone https://github.com/admas/CryptoCLI.git
cd CryptoCLI

# Install the package
pip install -e .
```

## Configuration

CryptoCLI requires a CoinGecko API key to function. Create a `.env` file in your home directory or project root with:

```
COINGECKO_BASE_URL=official_coingecko_api_url
COINGECKO_API_KEY=your_api_key_here
```

You can get an API key by signing up at [CoinGecko Pro](https://www.coingecko.com/en/api/pricing).

## Usage

### Getting Current Prices

```bash
# Get the current price for Bitcoin in USD
CryptoCLI price bitcoin

# Get prices for multiple cryptocurrencies
CryptoCLI price bitcoin ethereum solana

# Get prices in multiple currencies
CryptoCLI price bitcoin ethereum --currencies usd,eur,jpy

# Get detailed market information
CryptoCLI price bitcoin --detailed
```

### Viewing Historical Data

```bash
# Get weekly historical data for Bitcoin
CryptoCLI history bitcoin

# Get monthly data in EUR
CryptoCLI history ethereum --period month --currency eur

# Get custom period data and save to file
CryptoCLI history solana --period custom --days 45 --save
```

### Getting OHLC Chart Data

```bash
# Get 7-day OHLC data for Bitcoin
CryptoCLI ohlc bitcoin

# Get 30-day OHLC data for Ethereum in euros
CryptoCLI ohlc ethereum --currency eur --days 30

# Get OHLC data and save to file
CryptoCLI ohlc cardano --days 90 --save
```

### Searching for Cryptocurrencies

```bash
# Search for Bitcoin
CryptoCLI search bitcoin

# Search by symbol
CryptoCLI search btc

# Limit the number of results
CryptoCLI search dog --limit 5
```

### Checking Configuration

```bash
# Display current configuration
CryptoCLI config
```

### Global Crypto Data

```bash
# Get global cryptocurrency data
CryptoCLI global-data
```

### Supported Fiat Currencies

```bash
# Display supported fiat currencies for price conversion
CryptoCLI fiat
```

### Token Details

```bash
# Get detailed data for a token by contract address
CryptoCLI token 0x1f9840a85d5af5bf1d1762f925bdaddc4201f984
```

### Asset Platforms

```bash
# List all asset platforms supported by CoinGecko
CryptoCLI platforms
```

### Supported Currencies

```bash
# List all supported fiat currencies for price conversions
CryptoCLI currencies
```

## Command Reference

### `price`

Get current prices for specific coins.

```
CryptoCLI price COIN_IDS... [OPTIONS]
```

Options:

- `--currencies, -c`: Comma-separated list of currencies (default: usd)
- `--detailed, -d`: Show more detailed information including 24h change

### `history`

Get historical price data for a specific coin.

```
CryptoCLI history COIN_ID [OPTIONS]
```

Options:

- `--currency, -c`: Currency to get data in (default: usd)
- `--period, -p`: Time period for historical data (day, week, month, year, custom)
- `--days, -d`: Custom number of days (for custom period)
- `--save, -s`: Save historical data to a JSON file
- `--output, -o`: Filename to save data to (requires --save)

### `ohlc`

Get OHLC (Open, High, Low, Close) chart data for a specific coin.

```
CryptoCLI ohlc COIN_ID [OPTIONS]
```

Options:

- `--currency, -c`: Currency to get data in (default: usd)
- `--days, -d`: Number of days of data (1,7,14,30,90,180,365)
- `--save, -s`: Save OHLC data to a JSON file
- `--output, -o`: Filename to save data (requires --save)

### `search`

Search for cryptocurrencies by name or symbol.

```
CryptoCLI search QUERY [OPTIONS]
```

Options:

- `--limit, -l`: Maximum number of results to display (default: 10)

### `config`

Display current configuration.

```
CryptoCLI config
```

### `global-data`

Show global cryptocurrency market data.

```
CryptoCLI global-data [OPTIONS]
```

Options:

- `--save, -s`: Save global market data to a JSON file
- `--output, -o`: Filename to save data (requires --save)

### `fiat`

Display a list of fiat currencies supported for price conversions.

```
CryptoCLI fiat
```

### `token`

Get detailed data for a token using its contract address.

```
CryptoCLI token CONTRACT_ADDRESS [OPTIONS]
```

Options:

- `--platform, -p`: Asset platform (default: ethereum)
- `--currency, -c`: Currency for market data (default: usd)
- `--tickers/--no-tickers`: Display exchange ticker information (default: enabled)
- `--tickers-limit, -t`: Maximum number of exchange tickers to display (default: 5)
- `--save, -s`: Save token data to a JSON file
- `--output, -o`: Filename to save data (requires --save)

### `platforms`

List all asset platforms (blockchains) supported by CoinGecko.

```
CryptoCLI platforms [OPTIONS]
```

Options:

- `--format, -f`: Output format (table or list; default: table)
- `--query, -q`: Filter platforms by name or ID
- `--save, -s`: Save platforms data to a JSON file
- `--output, -o`: Filename to save data (requires --save)

### `currencies`

List all supported fiat currencies for price conversions.

```
CryptoCLI currencies [OPTIONS]
```

Options:

- `--save, -s`: Save list of currencies to a JSON file
- `--output, -o`: Filename to save data (requires --save)

## Data Export

Many commands support exporting data to JSON files for further analysis:

```bash
# Save historical data
CryptoCLI history bitcoin --save --output bitcoin_history.json

# Save OHLC data
CryptoCLI ohlc ethereum --save --output ethereum_ohlc.json
```

## Rate Limiting

CryptoCLI respects the CoinGecko API rate limits by implementing a 1.5-second delay between requests by default. This ensures the application remains functional even during extended use.

## Known Limitations

- The CoinGecko free tier has more restrictive rate limits
- Some advanced data may require a paid API plan
- OHLC data is only available for specific time periods supported by the API

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [CoinGecko](https://www.coingecko.com/) for providing the cryptocurrency data API
- [Click](https://click.palletsprojects.com/) for the CLI framework
- [Rich](https://rich.readthedocs.io/) for terminal formatting

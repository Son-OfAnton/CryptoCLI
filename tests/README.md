# CryptoCLI Tests

This directory contains tests for the CryptoCLI application.

## Running Tests

You can run the tests using the provided `run_tests.py` script:

```bash
python run_tests.py
```

Or directly using pytest:

```bash
pytest tests/ -v
```

## Test Structure

- `conftest.py` - Contains shared pytest fixtures
- `test_price.py` - Tests for price fetching functionality
  - `TestSingleCryptocurrencyPrice` - Tests for fetching a single cryptocurrency price
  - `TestMultipleCryptocurrenciesPrice` - Tests for fetching multiple cryptocurrency prices
  - `TestMultipleCryptosEdgeCases` - Edge case tests for multiple cryptocurrencies

## Test Coverage

The test suite covers:

1. **Single Cryptocurrency Tests:**
   - Basic price fetching
   - Display formatting
   - Error handling
   - Different currency formats
   - CLI command integration

2. **Multiple Cryptocurrencies Tests:**
   - Fetching prices for multiple cryptocurrencies at once
   - Sorting and display formatting
   - Detailed market data for multiple cryptocurrencies
   - Handling missing cryptocurrencies
   - API limits for large requests
   - CLI command integration for multiple cryptocurrencies

3. **Edge Cases:**
   - Case sensitivity handling
   - Duplicate cryptocurrency IDs
   - Large numbers of cryptocurrencies
   - Unusual inputs (empty lists, None values, etc.)

## Adding New Tests

When adding new tests:

1. Create a new test file in the `tests/` directory or add to existing ones
2. Import the necessary modules and fixtures from `conftest.py`
3. Create test classes and methods following pytest naming conventions
4. Use the mock fixtures to avoid making actual API calls

## Coverage Reports

To generate a test coverage report, run:

```bash
pytest tests/ --cov=CryptoCLI --cov-report=html:coverage_html
```

This will create an HTML coverage report in the `coverage_html` directory.
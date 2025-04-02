# CryptoCLI Test Suite

Comprehensive testing framework for the CryptoCLI application.

## Overview

The CryptoCLI test suite provides extensive coverage of all application functionality, ensuring reliability and correctness. It uses pytest as the primary testing framework along with mocking to avoid making actual API calls during testing.

## Running Tests

### Using the Run Script

The simplest way to run all tests is using the provided script:

```bash
python run_tests.py
```

This will run all tests and generate a coverage report.

### Using pytest Directly

You can also run tests using pytest commands:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_price.py

# Run with increased verbosity
pytest -v

# Run with coverage report
pytest --cov=CryptoCLI

# Generate HTML coverage report
pytest --cov=CryptoCLI --cov-report=html:coverage_html
```

## Test Fixtures

The test suite uses fixtures (defined in `conftest.py`) to provide consistent test data and mocks:

### Mock API Responses

- `mock_simple_price_response`: Mock response for the CoinGecko simple/price endpoint
- `mock_detailed_price_response`: Mock response for the CoinGecko markets endpoint
- `mock_historical_response`: Mock response for historical data
- `mock_ohlc_response`: Mock response for OHLC chart data
- `mock_search_response`: Mock response for cryptocurrency search
- `mock_empty_response`: Empty response for testing error handling
- `mock_error_response`: Simulated API error response

### Utility Fixtures

- `mock_api`: Mock for the CoinGecko API class
- `capture_stdout`: For testing console output
- `setup_environment`: Sets up test environment variables

## Test Coverage

The test suite provides comprehensive coverage of:

### Price Module Tests (`test_price.py`)

- **Single Cryptocurrency Price Tests**:
  - Basic price fetching
  - Display formatting
  - Multiple currencies
  - Error handling
  
- **Multiple Cryptocurrencies Tests**:
  - Fetching multiple prices
  - Sorting and display
  - Detailed market data
  - Large number of cryptocurrencies
  
- **Edge Cases**:
  - Case sensitivity
  - Duplicate cryptocurrency IDs
  - API limits
  - Invalid inputs

### Search Module Tests (`test_search.py`, `test_search_by_name_symbol.py`, `test_search_combined.py`)

- **Basic Search Functionality**:
  - Search by cryptocurrency name
  - Search by symbol
  - Result limiting
  - Error handling
  
- **Name and Symbol Search Tests**:
  - Full name matching
  - Symbol matching
  - Partial name matching
  - Case insensitivity
  
- **Comprehensive Tests**:
  - Suggestion functionality
  - CLI integration
  - Display formatting consistency
  - Error feedback

### OHLC Module Tests (`test_ohlc.py`)

- **Data Retrieval**:
  - Basic OHLC data fetching
  - Different time periods
  - Parameter validation
  
- **Display Formatting**:
  - Tabular data display
  - Summary statistics
  - ASCII chart generation
  
- **Data Export**:
  - JSON file saving
  - Custom filenames
  
- **Error Handling**:
  - API errors
  - Invalid parameters
  - Empty responses

## Mock Strategy

The test suite uses strategic mocking to avoid making actual API calls:

1. **API Mocking**: All calls to the CoinGecko API are mocked
2. **Response Simulation**: Predefined responses mimic actual API data
3. **Console Capture**: Output to the console is captured for verification
4. **Environment Simulation**: Environment variables are temporarily set for testing

## Adding New Tests

When adding new tests:

1. **Create Test Functions**: Add new test functions following the naming convention `test_*`
2. **Use Fixtures**: Leverage existing fixtures from `conftest.py`
3. **Mock External Calls**: All external API calls should be mocked
4. **Test Edge Cases**: Include tests for error conditions and edge cases
5. **Verify Output**: Check both return values and console output

Example test function:

```python
def test_new_feature(mock_api, capture_stdout):
    # Setup mock responses
    mock_api.some_method.return_value = {"expected": "data"}
    
    # Call the function under test
    result = your_feature_function()
    
    # Verify the result
    assert result == expected_result
    
    # Verify console output if applicable
    output = capture_stdout.getvalue()
    assert "Expected output" in output
```

## Test Coverage Goals

The test suite aims to maintain:

- At least 90% overall code coverage
- 100% coverage of core API interactions
- 100% coverage of error handling code
- Comprehensive CLI command testing

## Continuous Integration

The test suite is designed to run in CI/CD pipelines:

- GitHub Actions workflow runs all tests on each pull request
- Coverage reports are generated and archived
- Test failures prevent merging of pull requests

## Troubleshooting Tests

Common issues:

- **Rate Limit Errors**: Ensure API calls are properly mocked
- **Environment Variables**: Check that `conftest.py` sets required environment variables
- **Timestamp Comparison**: Use relative time comparisons to avoid test brittleness
- **Console Output Tests**: Rich console formatting may affect string matching

## License

The test suite is part of the CryptoCLI project and is licensed under the MIT License.
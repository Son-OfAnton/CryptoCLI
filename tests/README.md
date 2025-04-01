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

## Adding New Tests

When adding new tests:

1. Create a new test file in the `tests/` directory
2. Import the necessary modules and fixtures
3. Create test classes and methods following pytest naming conventions

## Coverage Reports

To generate a test coverage report, run:

```bash
pytest tests/ --cov=CryptoCLI --cov-report=html:coverage_html
```

This will create an HTML coverage report in the `coverage_html` directory.

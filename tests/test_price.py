"""
Tests for the price fetching functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
import json
from rich.console import Console
import io
import sys

# Import the modules to test
from price import get_current_prices, get_prices_with_change
from api import CoinGeckoAPI


class TestSingleCryptocurrencyPrice:
    """Test cases for fetching the price of a single cryptocurrency in a single fiat currency."""

    def test_get_single_crypto_price(self, mock_api, mock_simple_price_response, monkeypatch):
        """
        Test fetching the price of a single cryptocurrency with a single fiat currency.
        Should return price data in the expected format.
        """
        # Setup the mock API to return our test data
        mock_api.get_price.return_value = mock_simple_price_response
        
        # Create a new Console that writes to a string buffer so we can capture the output
        console_output = io.StringIO()
        test_console = Console(file=console_output)
        
        # Patch both the API instance and the console used for display
        with patch('CryptoCLI.price.api', mock_api):
            with patch('CryptoCLI.price.console', test_console):
                # Call the function with a single crypto and single currency
                result = get_current_prices(['bitcoin'], ['usd'], display=True)
                
                # Check the API was called with the correct parameters
                mock_api.get_price.assert_called_once_with(['bitcoin'], ['usd'])
                
                # Verify the result matches our mock data
                assert result == mock_simple_price_response
                
                # Check the output contains the expected values
                output = console_output.getvalue()
                assert "Current Cryptocurrency Prices" in output
                assert "bitcoin" in output
                assert "$57,234.78" in output

    def test_get_single_crypto_price_no_display(self, mock_api, mock_simple_price_response):
        """
        Test fetching the price without displaying it.
        Should return price data but not produce console output.
        """
        # Setup the mock API to return our test data
        mock_api.get_price.return_value = mock_simple_price_response
        
        # Create a string buffer to check if anything is written
        console_output = io.StringIO()
        test_console = Console(file=console_output)
        
        # Patch both the API instance and the console
        with patch('CryptoCLI.price.api', mock_api):
            with patch('CryptoCLI.price.console', test_console):
                # Call with display=False
                result = get_current_prices(['bitcoin'], ['usd'], display=False)
                
                # Verify the result matches our mock data
                assert result == mock_simple_price_response
                
                # Verify no output was produced
                output = console_output.getvalue()
                assert output == ""

    def test_get_single_crypto_detailed_price(self, mock_api, mock_detailed_price_response):
        """
        Test fetching detailed price information for a single cryptocurrency.
        Should return and display price with market data.
        """
        # Setup the mock API to return our test data
        mock_api.get_coin_markets.return_value = mock_detailed_price_response
        
        # Create a string buffer to capture console output
        console_output = io.StringIO()
        test_console = Console(file=console_output)
        
        # Patch the necessary components
        with patch('CryptoCLI.price.api', mock_api):
            with patch('CryptoCLI.price.console', test_console):
                # Call the function to get detailed price data
                result = get_prices_with_change(['bitcoin'], 'usd')
                
                # Check the API was called correctly
                mock_api.get_coin_markets.assert_called_once()
                
                # Verify the result structure
                assert 'bitcoin' in result
                assert 'usd' in result['bitcoin']
                assert 'usd_24h_change' in result['bitcoin']
                assert 'market_cap_rank' in result['bitcoin']
                
                # Check the output contains the expected data
                output = console_output.getvalue()
                assert "Bitcoin" in output
                assert "BTC" in output
                assert "$57,234.78" in output
                assert "-0.98%" in output
                assert "1.12B" in output  # Formatted market cap

    def test_api_error_handling(self, mock_api):
        """
        Test that API errors are properly caught and handled.
        Should return empty dictionary and display error message.
        """
        # Setup the mock to raise an exception
        mock_api.get_price.side_effect = Exception("API request failed")
        
        # Create a string buffer to capture console output
        console_output = io.StringIO()
        test_console = Console(file=console_output)
        
        # Patch the necessary components
        with patch('CryptoCLI.price.api', mock_api):
            with patch('CryptoCLI.price.console', test_console):
                # Call the function which should handle the error
                result = get_current_prices(['bitcoin'], ['usd'], display=True)
                
                # Verify an empty dict is returned on error
                assert result == {}
                
                # Check error message was displayed
                output = console_output.getvalue()
                assert "Error" in output
                assert "API request failed" in output

    def test_invalid_coin_id(self, mock_api, mock_empty_response):
        """
        Test behavior with invalid coin ID.
        Should display a warning message about no price data.
        """
        # Setup the mock to return empty response
        mock_api.get_price.return_value = mock_empty_response
        
        # Create a string buffer to capture console output
        console_output = io.StringIO()
        test_console = Console(file=console_output)
        
        # Patch the necessary components
        with patch('CryptoCLI.price.api', mock_api):
            with patch('CryptoCLI.price.console', test_console):
                # Call with a presumably invalid coin ID
                result = get_current_prices(['invalid_coin_id'], ['usd'], display=True)
                
                # Should return the empty dict
                assert result == {}
                
                # Should show a warning
                output = console_output.getvalue()
                assert "Warning" in output
                assert "No price data found" in output

    @pytest.mark.parametrize(
        "coin_id,currency",
        [
            ("ethereum", "usd"),
            ("bitcoin", "eur"),
            ("litecoin", "gbp"),
            ("ripple", "jpy"),
        ]
    )
    def test_different_currencies(self, coin_id, currency, mock_api):
        """
        Test fetching prices with different crypto and fiat combinations.
        Should correctly format according to the currency.
        """
        # Create custom response for the test case
        mock_response = {
            coin_id: {
                currency: 1234.56
            }
        }
        mock_api.get_price.return_value = mock_response
        
        # Create a string buffer to capture console output
        console_output = io.StringIO()
        test_console = Console(file=console_output)
        
        # Patch the necessary components
        with patch('CryptoCLI.price.api', mock_api):
            with patch('CryptoCLI.price.console', test_console):
                # Call with the test parameters
                result = get_current_prices([coin_id], [currency], display=True)
                
                # Verify correct API call
                mock_api.get_price.assert_called_once_with([coin_id], [currency])
                
                # Verify result
                assert result == mock_response
                
                # Check output formatting based on currency
                output = console_output.getvalue()
                if currency == "usd":
                    assert "$1,234.56" in output
                elif currency == "eur":
                    assert "€1,234.56" in output
                elif currency == "gbp":
                    assert "£1,234.56" in output
                elif currency == "jpy":
                    # JPY typically doesn't use decimal places
                    assert "1,234" in output

    def test_cli_integration(self, monkeypatch, mock_api, mock_simple_price_response):
        """
        Test the integration with the CLI command.
        This tests the price command in the main CLI interface.
        """
        from click.testing import CliRunner
        from main import price
        
        # Setup the mock API
        mock_api.get_price.return_value = mock_simple_price_response
        
        with patch('CryptoCLI.price.api', mock_api):
            # Use CliRunner to test the Click command
            runner = CliRunner()
            result = runner.invoke(price, ['bitcoin', '--currencies', 'usd'])
            
            # Check for successful execution
            assert result.exit_code == 0
            
            # Verify the output contains the expected price
            assert "bitcoin" in result.output
            assert "$57,234.78" in result.output

if __name__ == "__main__":
    pytest.main()
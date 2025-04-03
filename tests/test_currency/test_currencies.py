"""
Tests for the currencies functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
import json
import os
from io import StringIO
import sys

# Import modules to test
from currencies import get_supported_currencies, display_supported_currencies, save_currencies_data

@pytest.fixture
def mock_currencies_response():
    """Mock response for the CoinGecko supported_vs_currencies endpoint"""
    return [
        "usd", "aed", "ars", "aud", "bch", "bdt", "bhd", "bmd", "bnb", "brl",
        "btc", "cad", "chf", "clp", "cny", "czk", "dkk", "dot", "eos", "eth",
        "eur", "gbp", "hkd", "huf", "idr", "ils", "inr", "jpy", "krw", "kwd",
        "lkr", "ltc", "mmk", "mxn", "myr", "ngn", "nok", "nzd", "php", "pkr",
        "pln", "rub", "sar", "sek", "sgd", "thb", "try", "twd", "uah", "vef",
        "vnd", "xag", "xau", "xdr", "xlm", "xrp", "yfi", "zar", "bits", "link",
        "sats"
    ]


class TestCurrenciesRetrieval:
    """Test cases for fetching supported currencies."""

    def test_get_currencies_basic(self, mock_api, mock_currencies_response):
        """
        Test fetching the list of supported currencies.
        Should return data in the expected format.
        """
        # Setup the mock API to return our test data
        mock_api.get_supported_vs_currencies.return_value = mock_currencies_response
        
        # Call the function with display off to check return value only
        with patch('currencies.api', mock_api):
            with patch('currencies.display_supported_currencies') as mock_display:
                result = get_supported_currencies(display=False, save=False)
                
                # Check the API was called
                mock_api.get_supported_vs_currencies.assert_called_once()
                
                # Verify display function wasn't called
                mock_display.assert_not_called()
                
                # Verify the result matches our mock data
                assert result == mock_currencies_response
                assert len(result) == len(mock_currencies_response)
                assert "usd" in result
                assert "eur" in result
                assert "btc" in result

    def test_get_currencies_with_display(self, mock_api, mock_currencies_response):
        """
        Test fetching currencies with display enabled.
        Should call the display function.
        """
        # Setup the mock API to return our test data
        mock_api.get_supported_vs_currencies.return_value = mock_currencies_response
        
        # Call the function with display on
        with patch('currencies.api', mock_api):
            with patch('currencies.display_supported_currencies') as mock_display:
                result = get_supported_currencies(display=True, save=False)
                
                # Verify display function was called with the right data
                mock_display.assert_called_once_with(mock_currencies_response)
                
                # Verify the result matches our mock data
                assert result == mock_currencies_response

    def test_get_currencies_with_save(self, mock_api, mock_currencies_response, tmp_path):
        """
        Test fetching currencies with save enabled.
        Should call the save function with the right parameters.
        """
        # Setup the mock API to return our test data
        mock_api.get_supported_vs_currencies.return_value = mock_currencies_response
        
        # Create a temporary file path
        test_output = tmp_path / "test_currencies.json"
        
        # Call the function with save on
        with patch('currencies.api', mock_api):
            with patch('currencies.display_supported_currencies') as mock_display:
                with patch('currencies.save_currencies_data') as mock_save:
                    result = get_supported_currencies(display=True, save=True, output=str(test_output))
                    
                    # Verify save function was called with the right data
                    mock_save.assert_called_once_with(mock_currencies_response, str(test_output))
                    
                    # Verify the result matches our mock data
                    assert result == mock_currencies_response

    def test_get_currencies_empty_response(self, mock_api):
        """
        Test handling of empty response from the API.
        Should display an error and return None.
        """
        # Setup the mock API to return an empty response
        mock_api.get_supported_vs_currencies.return_value = []
        
        # Call the function
        with patch('currencies.api', mock_api):
            with patch('currencies.print_error') as mock_error:
                result = get_supported_currencies(display=True, save=False)
                
                # Verify error was displayed
                mock_error.assert_called_once_with("No supported currencies found.")
                
                # Verify the function returns None
                assert result is None

    def test_get_currencies_api_error(self, mock_api):
        """
        Test handling of API error.
        Should display an error message and return None.
        """
        # Setup the mock API to raise an exception
        mock_api.get_supported_vs_currencies.side_effect = Exception("API Error")
        
        # Call the function
        with patch('currencies.api', mock_api):
            with patch('currencies.print_error') as mock_error:
                result = get_supported_currencies(display=True, save=False)
                
                # Verify error was displayed
                mock_error.assert_called_once_with("Failed to retrieve supported currencies: API Error")
                
                # Verify the function returns None
                assert result is None


class TestCurrencyDisplay:
    """Test cases for displaying currencies."""

    def test_display_currencies(self, mock_currencies_response):
        """
        Test that the display function formats currencies correctly.
        Should output a table with currency codes and categories.
        """
        # Create a StringIO object to capture stdout
        captured_output = StringIO()
        
        # Patch the console
        with patch('currencies.console') as mock_console:
            # Call the function
            display_supported_currencies(mock_currencies_response)
            
            # Verify that console.print was called at least twice
            # Once for the table, once for the totals
            assert mock_console.print.call_count >= 2
            
            # Verify the table was created with the right title
            calls = mock_console.print.call_args_list
            table_call = calls[0]
            assert "Supported Fiat Currencies" in str(table_call)
            
            # Verify the total count message
            total_call = calls[1]
            assert f"Total supported currencies: {len(mock_currencies_response)}" in str(total_call)


class TestCurrencySaving:
    """Test cases for saving currency data."""

    def test_save_currencies_data_default_filename(self, mock_currencies_response, tmp_path, monkeypatch):
        """
        Test saving currencies with default filename.
        Should create a JSON file with the right structure.
        """
        # Change to the temporary directory
        monkeypatch.chdir(tmp_path)
        
        # Patch the console
        with patch('currencies.console') as mock_console:
            # Call the function
            save_currencies_data(mock_currencies_response)
            
            # Check if the file exists
            default_file = tmp_path / "supported_currencies.json"
            assert default_file.exists()
            
            # Verify content of the saved file
            with open(default_file, 'r') as f:
                saved_data = json.load(f)
                
                # Check structure of saved data
                assert "supported_currencies" in saved_data
                assert "count" in saved_data
                assert saved_data["count"] == len(mock_currencies_response)
                assert len(saved_data["supported_currencies"]) == len(mock_currencies_response)
                assert "usd" in saved_data["supported_currencies"]
            
            # Verify success message was shown
            mock_console.print.assert_called_once()
            assert "Currency data saved to" in str(mock_console.print.call_args)

    def test_save_currencies_data_custom_filename(self, mock_currencies_response, tmp_path):
        """
        Test saving currencies with custom filename.
        Should create a JSON file with the specified name.
        """
        # Create a custom filename
        custom_file = tmp_path / "custom_currencies.json"
        
        # Patch the console
        with patch('currencies.console') as mock_console:
            # Call the function
            save_currencies_data(mock_currencies_response, str(custom_file))
            
            # Check if the file exists
            assert custom_file.exists()
            
            # Verify content of the saved file
            with open(custom_file, 'r') as f:
                saved_data = json.load(f)
                assert "supported_currencies" in saved_data
                assert len(saved_data["supported_currencies"]) == len(mock_currencies_response)
            
            # Verify success message was shown with custom filename
            mock_console.print.assert_called_once()
            assert str(custom_file) in str(mock_console.print.call_args)

    def test_save_currencies_data_error(self, mock_currencies_response):
        """
        Test error handling when saving currencies.
        Should display an error message.
        """
        # Create a filename that points to a directory that doesn't exist
        invalid_file = "/nonexistent/directory/currencies.json"
        
        # Patch the error display
        with patch('currencies.print_error') as mock_error:
            # Call the function
            save_currencies_data(mock_currencies_response, invalid_file)
            
            # Verify error was displayed
            mock_error.assert_called_once()
            assert "Failed to save currency data" in str(mock_error.call_args)


class TestCLICommand:
    """Test cases for the currencies CLI command."""

    def test_currencies_command_basic(self, mock_api, mock_currencies_response, monkeypatch):
        """
        Test the currencies command without options.
        Should call get_supported_currencies with the right parameters.
        """
        # Import the CLI runner from Click
        from click.testing import CliRunner
        
        # Create a runner
        runner = CliRunner()
        
        # Import the CLI function
        from main import currencies
        
        # Setup the mock API
        mock_api.get_supported_vs_currencies.return_value = mock_currencies_response
        
        # Patch the get_supported_currencies function
        with patch('main.get_supported_currencies') as mock_function:
            # Run the command
            result = runner.invoke(currencies)
            
            # Verify the function was called with the right parameters
            mock_function.assert_called_once_with(
                display=True,
                save=False,
                output=None
            )
            
            # Verify exit code
            assert result.exit_code == 0

    def test_currencies_command_with_save(self, mock_api, mock_currencies_response, monkeypatch):
        """
        Test the currencies command with --save option.
        Should call get_supported_currencies with save=True.
        """
        # Import the CLI runner from Click
        from click.testing import CliRunner
        
        # Create a runner
        runner = CliRunner()
        
        # Import the CLI function
        from main import currencies
        
        # Setup the mock API
        mock_api.get_supported_vs_currencies.return_value = mock_currencies_response
        
        # Patch the get_supported_currencies function
        with patch('main.get_supported_currencies') as mock_function:
            # Run the command with --save
            result = runner.invoke(currencies, ['--save'])
            
            # Verify the function was called with save=True
            mock_function.assert_called_once_with(
                display=True,
                save=True,
                output=None
            )
            
            # Verify exit code
            assert result.exit_code == 0

    def test_currencies_command_with_custom_output(self, mock_api, mock_currencies_response, monkeypatch):
        """
        Test the currencies command with --save and --output options.
        Should call get_supported_currencies with the custom output path.
        """
        # Import the CLI runner from Click
        from click.testing import CliRunner
        
        # Create a runner
        runner = CliRunner()
        
        # Import the CLI function
        from main import currencies
        
        # Setup the mock API
        mock_api.get_supported_vs_currencies.return_value = mock_currencies_response
        
        # Patch the get_supported_currencies function
        with patch('main.get_supported_currencies') as mock_function:
            # Run the command with --save and --output
            result = runner.invoke(currencies, ['--save', '--output', 'custom.json'])
            
            # Verify the function was called with save=True and the custom output
            mock_function.assert_called_once_with(
                display=True,
                save=True,
                output='custom.json'
            )
            
            # Verify exit code
            assert result.exit_code == 0
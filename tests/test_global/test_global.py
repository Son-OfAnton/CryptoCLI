"""
Enhanced tests for the global cryptocurrency market data functionality.
"""
import pytest
from unittest.mock import patch, MagicMock, call
import json
import os
from io import StringIO
import sys
from datetime import datetime
from rich.table import Table
from rich.panel import Panel

# Import modules to test
from app.global_data import (
    get_global_data, 
    display_global_data, 
    save_global_data,
    create_market_overview_panel,
    create_dominance_table,
    create_stats_panel
)


@pytest.fixture
def mock_global_data_response():
    """Mock response for the CoinGecko global endpoint"""
    return {
        "data": {
            "active_cryptocurrencies": 10964,
            "upcoming_icos": 0,
            "ongoing_icos": 49,
            "ended_icos": 3376,
            "markets": 882,
            "active_market_pairs": 81523,
            "active_exchanges": 763,
            "total_market_cap": {
                "btc": 40248550.94390456,
                "eth": 656488456.1347343,
                "ltc": 20622533865.65674,
                "usd": 2367517219780.4238,
                "eur": 2172888421442.1423,
                "gbp": 1854302839759.2031,
                "jpy": 365193657321048.25,
            },
            "total_volume": {
                "btc": 2248874.558616693,
                "eth": 36682359.06118058,
                "ltc": 1152310291.0871193,
                "usd": 132303724662.15883,
                "eur": 121432064677.65305,
                "gbp": 103634720686.27625,
                "jpy": 20412198267772.15,
            },
            "market_cap_percentage": {
                "btc": 51.44636686570559,
                "eth": 15.795994374966863,
                "usdt": 4.762570502334856,
                "bnb": 2.1729321717896284,
                "sol": 1.6853662476848254,
                "xrp": 0.9914245474372709,
                "usdc": 0.9651908010222558,
                "steth": 0.8831730226497064,
                "ada": 0.7657673470151833,
                "doge": 0.5867593268889344
            },
            "market_cap_change_percentage_24h_usd": 0.36275252235818326,
            "updated_at": 1711110826,
            "ico_data": {
                "ongoing_icos": 49,
                "upcoming_icos": 0,
                "ended_icos": 3376
            }
        }
    }


@pytest.fixture
def mock_malformed_global_data_response():
    """Mock response with missing key data elements"""
    return {
        "data": {
            "active_cryptocurrencies": 10964,
            "upcoming_icos": 0,
            "ongoing_icos": 49,
            "ended_icos": 3376,
            # Missing total_market_cap
            # Missing total_volume
            "market_cap_percentage": {
                "btc": 51.44636686570559,
                "eth": 15.795994374966863
            },
            "updated_at": 1711110826
        }
    }


class TestGlobalDataRetrieval:
    """Test cases for fetching global cryptocurrency market data."""

    def test_get_global_data_basic(self, mock_api, mock_global_data_response):
        """
        Test fetching global market data.
        Should return data in the expected format.
        """
        # Setup the mock API to return our test data
        mock_api.get_global_data.return_value = mock_global_data_response
        
        # Call the function with display off to check return value only
        with patch('global_data.api', mock_api):
            with patch('global_data.display_global_data') as mock_display:
                result = get_global_data(display=False, save=False)
                
                # Check the API was called
                mock_api.get_global_data.assert_called_once()
                
                # Verify display function wasn't called
                mock_display.assert_not_called()
                
                # Verify the result matches our mock data
                assert result == mock_global_data_response['data']
                assert 'total_market_cap' in result
                assert 'market_cap_percentage' in result
                assert 'active_cryptocurrencies' in result
                
                # Verify important data values
                assert result['total_market_cap']['usd'] == 2367517219780.4238
                assert result['market_cap_percentage']['btc'] == 51.44636686570559
                assert result['active_cryptocurrencies'] == 10964

    def test_get_global_data_with_display(self, mock_api, mock_global_data_response):
        """
        Test fetching global market data with display enabled.
        Should call the display function.
        """
        # Setup the mock API to return our test data
        mock_api.get_global_data.return_value = mock_global_data_response
        
        # Call the function with display on
        with patch('global_data.api', mock_api):
            with patch('global_data.display_global_data') as mock_display:
                result = get_global_data(display=True, save=False)
                
                # Verify display function was called with the right data
                mock_display.assert_called_once_with(mock_global_data_response['data'])
                
                # Verify the result matches our mock data
                assert result == mock_global_data_response['data']

    def test_get_global_data_with_save(self, mock_api, mock_global_data_response, tmp_path):
        """
        Test fetching global market data with save enabled.
        Should call the save function with the right parameters.
        """
        # Setup the mock API to return our test data
        mock_api.get_global_data.return_value = mock_global_data_response
        
        # Create a temporary file path
        test_output = tmp_path / "test_global_data.json"
        
        # Call the function with save on
        with patch('global_data.api', mock_api):
            with patch('global_data.display_global_data'):
                with patch('global_data.save_global_data') as mock_save:
                    result = get_global_data(display=True, save=True, output=str(test_output))
                    
                    # Verify save function was called with the right data
                    mock_save.assert_called_once_with(mock_global_data_response['data'], str(test_output))
                    
                    # Verify the result matches our mock data
                    assert result == mock_global_data_response['data']

    def test_get_global_data_empty_response(self, mock_api):
        """
        Test handling of empty response from the API.
        Should display an error and return None.
        """
        # Setup the mock API to return an empty response
        mock_api.get_global_data.return_value = {}
        
        # Call the function
        with patch('global_data.api', mock_api):
            with patch('global_data.print_error') as mock_error:
                result = get_global_data(display=True, save=False)
                
                # Verify error was displayed
                mock_error.assert_called_once_with("No global market data found.")
                
                # Verify the function returns None
                assert result is None

    def test_get_global_data_no_data_key(self, mock_api):
        """
        Test handling of response without data key.
        Should display an error and return None.
        """
        # Setup the mock API to return a response without data key
        mock_api.get_global_data.return_value = {"status": {"error_code": 0}}
        
        # Call the function
        with patch('global_data.api', mock_api):
            with patch('global_data.print_error') as mock_error:
                result = get_global_data(display=True, save=False)
                
                # Verify error was displayed
                mock_error.assert_called_once_with("No global market data found.")
                
                # Verify the function returns None
                assert result is None

    def test_get_global_data_api_error(self, mock_api):
        """
        Test handling of API error.
        Should display an error message and return None.
        """
        # Setup the mock API to raise an exception
        mock_api.get_global_data.side_effect = Exception("API Error")
        
        # Call the function
        with patch('global_data.api', mock_api):
            with patch('global_data.print_error') as mock_error:
                result = get_global_data(display=True, save=False)
                
                # Verify error was displayed
                mock_error.assert_called_once_with("Failed to retrieve global market data: API Error")
                
                # Verify the function returns None
                assert result is None


class TestMarketOverviewPanel:
    """Test cases for creating the market overview panel."""
    
    def test_create_market_overview_panel(self, mock_global_data_response):
        """
        Test creating market overview panel with complete data.
        Should include all market metrics.
        """
        # Get the data part from the response
        data = mock_global_data_response['data']
        
        # Create the panel
        panel = create_market_overview_panel(data)
        
        # Verify it's a Panel object
        assert isinstance(panel, Panel)
        
        # Verify the panel title
        assert panel.title == "Global Cryptocurrency Market"
        
        # Verify the panel content has all expected data points
        panel_content = str(panel)
        assert "Total Market Cap:" in panel_content
        assert "24h Trading Volume:" in panel_content
        assert "Bitcoin Dominance:" in panel_content
        assert "Ethereum Dominance:" in panel_content
        assert "51.44%" in panel_content  # BTC dominance
        assert "15.79%" in panel_content  # ETH dominance
        assert "Last Updated:" in panel_content
    
    def test_create_market_overview_panel_with_missing_data(self, mock_malformed_global_data_response):
        """
        Test creating market overview panel with incomplete data.
        Should handle missing data gracefully.
        """
        # Get the data part from the response
        data = mock_malformed_global_data_response['data']
        
        # Patch the format_currency function to prevent errors
        with patch('global_data.format_currency', return_value="$0.00"):
            with patch('global_data.format_large_number', return_value="0"):
                # Create the panel
                panel = create_market_overview_panel(data)
                
                # Verify it's still a Panel object despite missing data
                assert isinstance(panel, Panel)
                
                # Verify the panel title is still correct
                assert panel.title == "Global Cryptocurrency Market"
                
                # Verify the panel includes what data it can
                panel_content = str(panel)
                assert "Bitcoin Dominance: 51.44%" in panel_content
                assert "Ethereum Dominance: 15.79%" in panel_content


class TestDominanceTable:
    """Test cases for creating the market dominance table."""
    
    def test_create_dominance_table(self, mock_global_data_response):
        """
        Test creating dominance table with complete data.
        Should include all cryptocurrencies sorted by dominance.
        """
        # Get the data part from the response
        data = mock_global_data_response['data']
        
        # Create the table
        table = create_dominance_table(data)
        
        # Verify it's a Table object
        assert isinstance(table, Table)
        
        # Verify the table title
        assert table.title == "Market Cap Dominance by Coin"
        
        # Verify the table content when converted to string
        table_content = str(table)
        
        # Check that coins are present and in the right order (sorted by dominance)
        assert "BTC" in table_content
        assert "ETH" in table_content
        assert "USDT" in table_content
        
        # BTC should come before ETH (higher dominance)
        btc_pos = table_content.find("BTC")
        eth_pos = table_content.find("ETH")
        assert btc_pos < eth_pos
    
    def test_create_dominance_table_empty_data(self):
        """
        Test creating dominance table with empty market cap percentage data.
        Should handle empty data gracefully.
        """
        # Create a data dict with empty market_cap_percentage
        data = {"market_cap_percentage": {}}
        
        # Create the table
        table = create_dominance_table(data)
        
        # Verify it's still a Table object despite empty data
        assert isinstance(table, Table)
        
        # Verify the table title is still correct
        assert table.title == "Market Cap Dominance by Coin"


class TestStatsPanel:
    """Test cases for creating the market statistics panel."""
    
    def test_create_stats_panel_with_complete_data(self, mock_global_data_response):
        """
        Test creating stats panel with complete data.
        Should include all market statistics.
        """
        # Get the data part from the response
        data = mock_global_data_response['data']
        
        # Create the panel
        panel = create_stats_panel(data)
        
        # Verify it's a Panel object
        assert isinstance(panel, Panel)
        
        # Verify the panel title
        assert panel.title == "Market Statistics"
        
        # Verify the panel content has all expected data points
        panel_content = str(panel)
        assert "Active Cryptocurrencies:" in panel_content
        assert "Active Exchanges:" in panel_content
        assert "Active Market Pairs:" in panel_content
        assert "ICO Statistics:" in panel_content
        
        # Check actual values
        assert "10964" in panel_content  # active cryptocurrencies
        assert "763" in panel_content    # active exchanges
        assert "81523" in panel_content  # active market pairs
        assert "49" in panel_content     # ongoing ICOs
    
    def test_create_stats_panel_missing_ico_data(self):
        """
        Test creating stats panel without ICO data.
        Should still display the available market statistics.
        """
        # Create data without ICO information
        data = {
            "active_cryptocurrencies": 10964,
            "active_exchanges": 763,
            "active_market_pairs": 81523
        }
        
        # Create the panel
        panel = create_stats_panel(data)
        
        # Verify it's still a Panel object
        assert isinstance(panel, Panel)
        
        # Verify panel contains the available information
        panel_content = str(panel)
        assert "Active Cryptocurrencies: 10964" in panel_content
        assert "Active Exchanges: 763" in panel_content
        assert "Active Market Pairs: 81523" in panel_content
        
        # Verify ICO Statistics section is not present
        assert "ICO Statistics:" not in panel_content


class TestGlobalDataDisplay:
    """Test cases for displaying global market data."""

    def test_display_global_data(self, mock_global_data_response):
        """
        Test that the display function formats global data correctly.
        Should output panels and tables with market data.
        """
        # Get the data part from the response
        data = mock_global_data_response['data']
        
        # Create mock panel and table objects
        mock_market_panel = MagicMock()
        mock_dominance_table = MagicMock()
        mock_stats_panel = MagicMock()
        
        # Patch the create functions
        with patch('global_data.create_market_overview_panel', return_value=mock_market_panel) as mock_panel_fn:
            with patch('global_data.create_dominance_table', return_value=mock_dominance_table) as mock_table_fn:
                with patch('global_data.create_stats_panel', return_value=mock_stats_panel) as mock_stats_fn:
                    with patch('global_data.console') as mock_console:
                        # Call the function
                        display_global_data(data)
                        
                        # Verify the create functions were called with the right data
                        mock_panel_fn.assert_called_once_with(data)
                        mock_table_fn.assert_called_once_with(data)
                        mock_stats_fn.assert_called_once_with(data)
                        
                        # Verify console prints were called in the right order
                        assert mock_console.print.call_count == 3
                        assert mock_console.print.call_args_list == [
                            call(mock_market_panel),
                            call(mock_dominance_table),
                            call(mock_stats_panel)
                        ]

    def test_display_global_data_with_missing_components(self, mock_malformed_global_data_response):
        """
        Test display function with incomplete data.
        Should still try to display available components.
        """
        # Get the data part from the response
        data = mock_malformed_global_data_response['data']
        
        # Create mock panel and table objects for available components
        mock_market_panel = MagicMock()
        mock_dominance_table = MagicMock()
        mock_stats_panel = MagicMock()
        
        # Patch the create and format functions
        with patch('global_data.create_market_overview_panel', return_value=mock_market_panel):
            with patch('global_data.create_dominance_table', return_value=mock_dominance_table):
                with patch('global_data.create_stats_panel', return_value=mock_stats_panel):
                    with patch('global_data.console') as mock_console:
                        with patch('global_data.format_currency', return_value="$0.00"):
                            with patch('global_data.format_large_number', return_value="0"):
                                # Call the function
                                display_global_data(data)
                                
                                # Verify console still prints available components
                                assert mock_console.print.call_count == 3


class TestGlobalDataSaving:
    """Test cases for saving global market data."""

    def test_save_global_data_default_filename(self, mock_global_data_response, tmp_path, monkeypatch):
        """
        Test saving global data with default timestamp-based filename.
        Should create a JSON file with the right structure.
        """
        # Get the data part from the response
        data = mock_global_data_response['data']
        
        # Change to the temporary directory
        monkeypatch.chdir(tmp_path)
        
        # Mock datetime to get a stable filename
        mock_timestamp = "20250403_123456"
        expected_filename = f"global_crypto_data_{mock_timestamp}.json"
        
        with patch('global_data.datetime') as mock_datetime:
            mock_dt = MagicMock()
            mock_dt.now.return_value.strftime.return_value = mock_timestamp
            mock_datetime.now.return_value = mock_dt
            mock_datetime.fromtimestamp.return_value.strftime.return_value = "2025-04-03 12:34:56 UTC"
            
            # Patch the console
            with patch('global_data.console') as mock_console:
                # Call the function
                save_global_data(data)
                
                # Check if the file exists
                default_file = tmp_path / expected_filename
                assert default_file.exists()
                
                # Verify content of the saved file
                with open(default_file, 'r') as f:
                    saved_data = json.load(f)
                    
                    # Check key data is in the saved file
                    assert 'total_market_cap' in saved_data
                    assert 'market_cap_percentage' in saved_data
                    assert 'updated_at' in saved_data
                    assert 'updated_at_formatted' in saved_data
                
                # Verify success message was shown
                mock_console.print.assert_called_once()
                assert "Global market data saved to" in str(mock_console.print.call_args)

    def test_save_global_data_custom_filename(self, mock_global_data_response, tmp_path):
        """
        Test saving global data with custom filename.
        Should create a JSON file with the specified name.
        """
        # Get the data part from the response
        data = mock_global_data_response['data']
        
        # Create a custom filename
        custom_file = tmp_path / "custom_global_data.json"
        
        # Mock datetime for timestamp formatting
        with patch('global_data.datetime') as mock_datetime:
            mock_datetime.fromtimestamp.return_value.strftime.return_value = "2025-04-03 12:34:56 UTC"
            
            # Patch the console
            with patch('global_data.console') as mock_console:
                # Call the function
                save_global_data(data, str(custom_file))
                
                # Check if the file exists
                assert custom_file.exists()
                
                # Verify content of the saved file
                with open(custom_file, 'r') as f:
                    saved_data = json.load(f)
                    assert 'total_market_cap' in saved_data
                    assert saved_data['total_market_cap']['usd'] == 2367517219780.4238
                    assert 'market_cap_percentage' in saved_data
                    assert 'updated_at_formatted' in saved_data
                    assert saved_data['updated_at_formatted'] == "2025-04-03 12:34:56 UTC"
                
                # Verify success message was shown with custom filename
                mock_console.print.assert_called_once()
                assert str(custom_file) in str(mock_console.print.call_args)

    def test_save_global_data_error(self, mock_global_data_response):
        """
        Test error handling when saving global data.
        Should display an error message.
        """
        # Get the data part from the response
        data = mock_global_data_response['data']
        
        # Create a filename that points to a directory that doesn't exist
        invalid_file = "/nonexistent/directory/global_data.json"
        
        # Patch the error display
        with patch('global_data.print_error') as mock_error:
            # Call the function
            save_global_data(data, invalid_file)
            
            # Verify error was displayed
            mock_error.assert_called_once()
            assert "Failed to save global market data" in str(mock_error.call_args)
    
    def test_save_global_data_with_missing_timestamp(self):
        """
        Test saving global data without timestamp field.
        Should still work and create a JSON file.
        """
        # Create data without updated_at field
        data = {
            "total_market_cap": {
                "usd": 2367517219780.4238
            },
            "market_cap_percentage": {
                "btc": 51.44636686570559
            }
        }
        
        # Create a temporary directory and file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            # Get the temporary filename
            filename = tmp.name
        
        try:
            # Mock datetime for timestamp stability
            with patch('global_data.datetime') as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = "20250403_123456"
                
                # Patch the console
                with patch('global_data.console') as mock_console:
                    # Call the function
                    save_global_data(data, filename)
                    
                    # Check if the file exists and has content
                    assert os.path.exists(filename)
                    with open(filename, 'r') as f:
                        saved_data = json.load(f)
                        assert 'total_market_cap' in saved_data
                        assert 'market_cap_percentage' in saved_data
                        
                        # The updated_at_formatted field should NOT be added
                        assert 'updated_at_formatted' not in saved_data
                    
                    # Verify success message
                    mock_console.print.assert_called_once()
        finally:
            # Clean up temporary file
            if os.path.exists(filename):
                os.remove(filename)


class TestCLICommand:
    """Test cases for the global-data CLI command."""

    def test_global_data_command_basic(self, mock_api, mock_global_data_response, monkeypatch):
        """
        Test the global-data command without options.
        Should call get_global_data with the right parameters.
        """
        # Import the CLI runner from Click
        from click.testing import CliRunner
        
        # Create a runner
        runner = CliRunner()
        
        # Import the CLI function
        from app.main import global_data
        
        # Setup the mock API
        mock_api.get_global_data.return_value = mock_global_data_response
        
        # Patch the get_global_data function
        with patch('main.get_global_data') as mock_function:
            # Run the command
            result = runner.invoke(global_data)
            
            # Verify the function was called with the right parameters
            mock_function.assert_called_once_with(
                display=True,
                save=False,
                output=None
            )
            
            # Verify exit code
            assert result.exit_code == 0

    def test_global_data_command_with_save(self, mock_api, mock_global_data_response, monkeypatch):
        """
        Test the global-data command with --save option.
        Should call get_global_data with save=True.
        """
        # Import the CLI runner from Click
        from click.testing import CliRunner
        
        # Create a runner
        runner = CliRunner()
        
        # Import the CLI function
        from app.main import global_data
        
        # Setup the mock API
        mock_api.get_global_data.return_value = mock_global_data_response
        
        # Patch the get_global_data function
        with patch('main.get_global_data') as mock_function:
            # Run the command with --save
            result = runner.invoke(global_data, ['--save'])
            
            # Verify the function was called with save=True
            mock_function.assert_called_once_with(
                display=True,
                save=True,
                output=None
            )
            
            # Verify exit code
            assert result.exit_code == 0

    def test_global_data_command_with_custom_output(self, mock_api, mock_global_data_response, monkeypatch):
        """
        Test the global-data command with --save and --output options.
        Should call get_global_data with the custom output path.
        """
        # Import the CLI runner from Click
        from click.testing import CliRunner
        
        # Create a runner
        runner = CliRunner()
        
        # Import the CLI function
        from app.main import global_data
        
        # Setup the mock API
        mock_api.get_global_data.return_value = mock_global_data_response
        
        # Patch the get_global_data function
        with patch('main.get_global_data') as mock_function:
            # Run the command with --save and --output
            result = runner.invoke(global_data, ['--save', '--output', 'custom_global.json'])
            
            # Verify the function was called with save=True and the custom output
            mock_function.assert_called_once_with(
                display=True,
                save=True,
                output='custom_global.json'
            )
            
            # Verify exit code
            assert result.exit_code == 0
    
    def test_global_data_command_help_text(self):
        """
        Test the help text for the global-data command.
        Should include clear instructions on usage and examples.
        """
        # Import the CLI runner from Click
        from click.testing import CliRunner
        
        # Create a runner
        runner = CliRunner()
        
        # Import the CLI function
        from app.main import global_data
        
        # Run the command with --help
        result = runner.invoke(global_data, ['--help'])
        
        # Verify exit code
        assert result.exit_code == 0
        
        # Verify help text contains key information
        assert "Show global cryptocurrency market data" in result.output
        assert "Examples:" in result.output
        assert "global-data" in result.output
        assert "--save" in result.output
        assert "--output" in result.output
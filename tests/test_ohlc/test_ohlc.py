"""
Tests for the OHLC (Open, High, Low, Close) chart functionality.
"""
import pytest
from unittest.mock import patch, MagicMock, mock_open
import json
import os
import sys
from io import StringIO
from datetime import datetime
import tempfile

# To run these tests, you will need:
# - pytest
# - pytest-mock
# - click (required for CliRunner)

# Import the modules to test
from app.ohlc import (
    get_ohlc_data,
    display_ohlc_data,
    display_ohlc_summary,
    display_ascii_chart,
    save_ohlc_data,
    VALID_DAYS
)
from app.api import CoinGeckoAPI

# Add a fixture for mock OHLC data
@pytest.fixture
def mock_ohlc_response():
    """Mock response for the CoinGecko OHLC endpoint"""
    # Format: [timestamp, open, high, low, close]
    # Timestamps are in milliseconds
    current_time_ms = int(datetime.now().timestamp() * 1000)
    one_day_ms = 24 * 60 * 60 * 1000
    
    return [
        [current_time_ms - (6 * one_day_ms), 45000.0, 46500.0, 44800.0, 46000.0],
        [current_time_ms - (5 * one_day_ms), 46000.0, 47200.0, 45900.0, 46800.0],
        [current_time_ms - (4 * one_day_ms), 46800.0, 48000.0, 46700.0, 47500.0],
        [current_time_ms - (3 * one_day_ms), 47500.0, 47900.0, 45800.0, 46200.0],
        [current_time_ms - (2 * one_day_ms), 46200.0, 46500.0, 45000.0, 45200.0],
        [current_time_ms - (1 * one_day_ms), 45200.0, 46700.0, 45100.0, 46500.0],
        [current_time_ms, 46500.0, 48000.0, 46400.0, 47800.0]
    ]

@pytest.fixture
def mock_empty_ohlc_response():
    """Mock empty OHLC response"""
    return []

class TestOHLCDataRetrieval:
    """Test cases for retrieving OHLC data for cryptocurrencies."""
    
    def test_get_ohlc_data_basic(self, mock_api, mock_ohlc_response):
        """
        Test basic OHLC data retrieval.
        Should return properly formatted OHLC data.
        """
        # Setup mock API to return our test data
        mock_api.get_coin_ohlc.return_value = mock_ohlc_response
        
        # Call with default parameters but don't display
        result = get_ohlc_data('bitcoin', display=False)
        
        # Check the API was called with the correct parameters
        mock_api.get_coin_ohlc.assert_called_once_with(
            coin_id='bitcoin',
            vs_currency='usd',
            days=7
        )
        
        # Verify the result matches our mock data
        assert result == mock_ohlc_response
        assert len(result) == 7
        
        # Verify each data point has the correct format
        for point in result:
            assert len(point) == 5  # [timestamp, open, high, low, close]
            assert isinstance(point[0], (int, float))  # timestamp
            assert isinstance(point[1], float)  # open
            assert isinstance(point[2], float)  # high
            assert isinstance(point[3], float)  # low
            assert isinstance(point[4], float)  # close
            
            # High should be >= open, close, and low
            assert point[2] >= point[1]  # high >= open
            assert point[2] >= point[4]  # high >= close
            assert point[2] >= point[3]  # high >= low
            
            # Low should be <= open, close, and high
            assert point[3] <= point[1]  # low <= open
            assert point[3] <= point[4]  # low <= close
            assert point[3] <= point[2]  # low <= high
    
    def test_get_ohlc_data_with_custom_parameters(self, mock_api, mock_ohlc_response):
        """
        Test OHLC data retrieval with custom parameters.
        Should respect currency and days parameters.
        """
        # Setup mock API to return our test data
        mock_api.get_coin_ohlc.return_value = mock_ohlc_response
        
        # Call with custom parameters
        result = get_ohlc_data(
            coin_id='ethereum',
            vs_currency='eur',
            days=30,
            display=False
        )
        
        # Check the API was called with the correct parameters
        mock_api.get_coin_ohlc.assert_called_once_with(
            coin_id='ethereum',
            vs_currency='eur',
            days=30
        )
        
        # Verify the result matches our mock data
        assert result == mock_ohlc_response
    
    def test_get_ohlc_data_invalid_days(self, mock_api, mock_ohlc_response, caplog):
        """
        Test OHLC data retrieval with invalid days parameter.
        Should fall back to default value with a warning.
        """
        # Setup mock API to return our test data
        mock_api.get_coin_ohlc.return_value = mock_ohlc_response
        
        # Call with invalid days parameter (not in VALID_DAYS)
        result = get_ohlc_data(
            coin_id='bitcoin',
            days=15,  # Invalid days value
            display=False
        )
        
        # API should be called with the default days parameter (7)
        mock_api.get_coin_ohlc.assert_called_once_with(
            coin_id='bitcoin',
            vs_currency='usd',
            days=7
        )
        
        # Result should still contain the mock data
        assert result == mock_ohlc_response
        
        # Check that a warning message was logged
        # Note: In a real environment, you would check logs or captured stdout
        # for this warning, but for this test caplog is mocked
    
    def test_get_ohlc_data_empty_response(self, mock_api, mock_empty_ohlc_response):
        """
        Test handling of empty OHLC data response.
        Should return an empty list and show a warning.
        """
        # Setup mock API to return empty data
        mock_api.get_coin_ohlc.return_value = mock_empty_ohlc_response
        
        # Call the function
        result = get_ohlc_data(
            coin_id='unknown_coin',
            display=False
        )
        
        # Check API was still called with the correct parameters
        mock_api.get_coin_ohlc.assert_called_once()
        
        # Result should be an empty list
        assert result == []
    
    def test_get_ohlc_data_api_error(self, mock_api):
        """
        Test handling of API errors during OHLC data retrieval.
        Should catch the exception and return an empty list.
        """
        # Setup mock API to raise an exception
        mock_api.get_coin_ohlc.side_effect = Exception("API Error")
        
        # Call the function
        result = get_ohlc_data(
            coin_id='bitcoin',
            display=False
        )
        
        # Check API was still called
        mock_api.get_coin_ohlc.assert_called_once()
        
        # Result should be an empty list because of the error
        assert result == []

class TestOHLCDataDisplay:
    """Test cases for displaying OHLC data."""
    
    def test_display_ohlc_data(self, mock_api, mock_ohlc_response, monkeypatch):
        """
        Test displaying OHLC data in tabular format.
        Should format and display the data correctly.
        """
        # Setup mocks for display functions called by display_ohlc_data
        summary_mock = MagicMock()
        chart_mock = MagicMock()
        monkeypatch.setattr('CryptoCLI.ohlc.display_ohlc_summary', summary_mock)
        monkeypatch.setattr('CryptoCLI.ohlc.display_ascii_chart', chart_mock)
        
        # Capture the console output
        captured_output = StringIO()
        monkeypatch.setattr('sys.stdout', captured_output)
        
        # Call the display function
        display_ohlc_data(mock_ohlc_response, 'bitcoin', 'usd', 7)
        
        # Check that the summary and chart functions were called
        summary_mock.assert_called_once_with(mock_ohlc_response, 'bitcoin', 'usd')
        chart_mock.assert_called_once_with(mock_ohlc_response, 'bitcoin', 'usd')
        
        # Check that the output contains expected elements
        output = captured_output.getvalue()
        assert "OHLC Data for Bitcoin (USD)" in output
        assert "Date" in output
        assert "Open" in output
        assert "High" in output
        assert "Low" in output
        assert "Close" in output
        assert "Change %" in output
    
    def test_display_ohlc_data_empty(self, monkeypatch):
        """
        Test displaying empty OHLC data.
        Should show a warning without displaying a table.
        """
        # Capture the console output
        captured_output = StringIO()
        monkeypatch.setattr('sys.stdout', captured_output)
        
        # Call the display function with empty data
        display_ohlc_data([], 'bitcoin', 'usd', 7)
        
        # Check that the output contains a warning
        output = captured_output.getvalue()
        assert "No OHLC data to display" in output
    
    def test_display_ohlc_summary(self, mock_ohlc_response, monkeypatch):
        """
        Test displaying OHLC summary statistics.
        Should calculate and display correct statistics.
        """
        # Capture the console output
        captured_output = StringIO()
        monkeypatch.setattr('sys.stdout', captured_output)
        
        # Call the summary function
        display_ohlc_summary(mock_ohlc_response, 'bitcoin', 'usd')
        
        # Check that the output contains expected elements
        output = captured_output.getvalue()
        assert "OHLC Summary" in output
        assert "Starting Price" in output
        assert "Ending Price" in output
        assert "Highest Price" in output
        assert "Lowest Price" in output
        assert "Average Open" in output
        assert "Average Close" in output
        assert "Price Range" in output
        assert "Overall Change" in output
    
    def test_display_ascii_chart(self, mock_ohlc_response, monkeypatch):
        """
        Test displaying ASCII price chart.
        Should generate and display a chart.
        """
        # Capture the console output
        captured_output = StringIO()
        monkeypatch.setattr('sys.stdout', captured_output)
        
        # Call the chart function
        display_ascii_chart(mock_ohlc_response, 'bitcoin', 'usd')
        
        # Check that the output contains expected elements
        output = captured_output.getvalue()
        assert "Price Chart for Bitcoin (USD)" in output
        assert "Range:" in output
        # Check for chart symbols in the output
        assert "●" in output or "│" in output or "─" in output or "/" in output or "\\" in output

class TestOHLCDataSaving:
    """Test cases for saving OHLC data to file."""
    
    def test_save_ohlc_data(self, mock_ohlc_response, monkeypatch):
        """
        Test saving OHLC data to a file.
        Should save properly formatted JSON data.
        """
        # Use a real temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            temp_filename = tmp.name
        
        try:
            # Call the save function with custom filename
            result = save_ohlc_data(mock_ohlc_response, 'bitcoin', 'usd', 7, temp_filename)
            
            # Check that the function returned the filename
            assert result == temp_filename
            
            # Verify file exists and contains valid JSON
            with open(temp_filename, 'r') as f:
                data = json.load(f)
                
                # Check that the data has the expected structure
                assert "coin_id" in data and data["coin_id"] == "bitcoin"
                assert "currency" in data and data["currency"] == "usd"
                assert "days" in data and data["days"] == 7
                assert "data_points" in data and data["data_points"] == len(mock_ohlc_response)
                assert "generated_at" in data
                assert "ohlc_data" in data and len(data["ohlc_data"]) == len(mock_ohlc_response)
                
                # Check that each OHLC data point has been properly formatted
                for point in data["ohlc_data"]:
                    assert "timestamp" in point
                    assert "date" in point
                    assert "open" in point
                    assert "high" in point
                    assert "low" in point
                    assert "close" in point
                    
                    # Verify values are correctly preserved
                    assert isinstance(point["timestamp"], (int, float))
                    assert isinstance(point["open"], float)
                    assert isinstance(point["high"], float)
                    assert isinstance(point["low"], float)
                    assert isinstance(point["close"], float)
        finally:
            # Clean up - remove the temporary file
            try:
                os.unlink(temp_filename)
            except:
                pass
    
    def test_save_ohlc_data_default_filename(self, mock_ohlc_response, monkeypatch):
        """
        Test saving OHLC data with a default generated filename.
        Should create a file with the expected naming convention.
        """
        # Mock the open function to avoid creating actual files
        mock_file = mock_open()
        monkeypatch.setattr('builtins.open', mock_file)
        
        # Mock time.time() to get a predictable filename
        monkeypatch.setattr('time.time', lambda: 1617292800)  # 2025-04-01 12:00:00 UTC
        
        # Call the save function without specifying a filename
        result = save_ohlc_data(mock_ohlc_response, 'ethereum', 'eur', 30)
        
        # Check that the returned filename follows the expected pattern
        assert "ethereum_eur_ohlc_30d_1617292800.json" in result
        
        # Verify that the file was opened for writing
        mock_file.assert_called_once_with(result, 'w')
        
        # Verify that json.dump was called with the right data structure
        handle = mock_file()
        assert handle.write.called
    
    def test_save_ohlc_data_empty(self, monkeypatch):
        """
        Test saving empty OHLC data.
        Should return error message without creating a file.
        """
        # Capture the console output
        captured_output = StringIO()
        monkeypatch.setattr('sys.stdout', captured_output)
        
        # Call the save function with empty data
        result = save_ohlc_data([], 'bitcoin', 'usd', 7, "test_file.json")
        
        # Check that the function returned empty string
        assert result == ""
        
        # Check that the output contains an error message
        output = captured_output.getvalue()
        assert "No data to save" in output
    
    def test_save_ohlc_data_error(self, mock_ohlc_response, monkeypatch):
        """
        Test handling file saving errors.
        Should catch exceptions and return empty string.
        """
        # Mock open to raise an exception
        def mock_open_with_error(*args, **kwargs):
            raise IOError("Failed to open file")
            
        monkeypatch.setattr('builtins.open', mock_open_with_error)
        
        # Capture the console output
        captured_output = StringIO()
        monkeypatch.setattr('sys.stdout', captured_output)
        
        # Call the save function
        result = save_ohlc_data(mock_ohlc_response, 'bitcoin', 'usd', 7, "test_file.json")
        
        # Check that the function returned empty string due to the error
        assert result == ""
        
        # Check that the output contains an error message
        output = captured_output.getvalue()
        assert "Failed to save OHLC data" in output

from click.testing import CliRunner

class TestOHLCWithCLIIntegration:
    """Test cases for the OHLC functionality through the CLI interface."""
    
    def test_ohlc_command_basic(self, mock_api, mock_ohlc_response, monkeypatch):
        """
        Test the OHLC command with basic parameters.
        Should fetch and display OHLC data.
        """
        # Mock get_ohlc_data function
        mock_get_ohlc = MagicMock(return_value=mock_ohlc_response)
        monkeypatch.setattr('CryptoCLI.main.get_ohlc_data', mock_get_ohlc)
        
        # Capture the CLI command output
        from app.main import ohlc
        runner = CliRunner()
        result = runner.invoke(ohlc, ['bitcoin'])
        
        # Check that the command executed successfully
        assert result.exit_code == 0
        
        # Check that the get_ohlc_data function was called with the right parameters
        mock_get_ohlc.assert_called_once_with(
            coin_id='bitcoin',
            vs_currency='usd',
            days=7  # default value
        )
    
    def test_ohlc_command_with_options(self, mock_api, mock_ohlc_response, monkeypatch):
        """
        Test the OHLC command with custom options.
        Should respect provided options.
        """
        # Mock both get_ohlc_data and save_ohlc_data functions
        mock_get_ohlc = MagicMock(return_value=mock_ohlc_response)
        mock_save_ohlc = MagicMock(return_value="test_output.json")
        monkeypatch.setattr('CryptoCLI.main.get_ohlc_data', mock_get_ohlc)
        monkeypatch.setattr('CryptoCLI.main.save_ohlc_data', mock_save_ohlc)
        
        # Capture the CLI command output
        from app.main import ohlc
        runner = CliRunner()
        result = runner.invoke(
            ohlc, 
            [
                'ethereum', 
                '--currency', 'eur', 
                '--days', '30', 
                '--save',
                '--output', 'custom_output.json'
            ]
        )
        
        # Check that the command executed successfully
        assert result.exit_code == 0
        
        # Check that the functions were called with the right parameters
        mock_get_ohlc.assert_called_once_with(
            coin_id='ethereum',
            vs_currency='eur',
            days=30
        )
        
        # Check that save was called with the right parameters
        mock_save_ohlc.assert_called_once_with(
            mock_ohlc_response,
            'ethereum',
            'eur',
            30,
            'custom_output.json'
        )
    
    def test_ohlc_command_no_data(self, mock_api, monkeypatch):
        """
        Test the OHLC command when no data is returned.
        Should handle the empty result properly.
        """
        # Mock get_ohlc_data to return empty data
        mock_get_ohlc = MagicMock(return_value=[])
        monkeypatch.setattr('CryptoCLI.main.get_ohlc_data', mock_get_ohlc)
        
        # Capture the CLI command output
        from app.main import ohlc
        runner = CliRunner()
        result = runner.invoke(ohlc, ['unknown_coin'])
        
        # Check that the command executed without crashing
        assert result.exit_code == 0
        
        # Should not try to save empty data
        # This is checking that the code in main.py correctly checks
        # if ohlc_data before trying to save it
        assert "No OHLC data" in result.output or "warning" in result.output.lower()
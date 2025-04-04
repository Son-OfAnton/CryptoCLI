"""
Tests for the companies' treasury holdings functionality.
"""
import pytest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
from app.companies import get_companies_treasury, display_companies_treasury, save_companies_treasury


class TestCompaniesTreasury:
    """Test cases for companies' treasury holdings functionality."""

    @patch("app.companies.api.get_companies_public_treasury")
    def test_get_bitcoin_treasury_success(self, mock_get_companies, mock_bitcoin_treasury_response):
        """Test getting Bitcoin treasury data successfully."""
        # Setup the mock to return Bitcoin test data
        mock_get_companies.return_value = mock_bitcoin_treasury_response
        
        # Call the function
        result = get_companies_treasury(coin_id="bitcoin", display=False)
        
        # Verify the result
        assert result is not None
        assert "total_holdings" in result
        assert result["total_holdings"] == 174045.0
        assert result["total_value_usd"] == 6962354677.5
        assert result["market_cap_dominance"] == 0.92
        assert len(result["companies"]) == 3
        
        # Check company data
        assert result["companies"][0]["name"] == "MicroStrategy"
        assert result["companies"][1]["name"] == "Tesla"
        assert result["companies"][2]["name"] == "Marathon Digital Holdings"
        
        # Verify the API was called with the correct coin ID
        mock_get_companies.assert_called_once_with("bitcoin")

    @patch("app.companies.api.get_companies_public_treasury")
    def test_get_ethereum_treasury_success(self, mock_get_companies, mock_ethereum_treasury_response):
        """Test getting Ethereum treasury data successfully."""
        # Setup the mock to return Ethereum test data
        mock_get_companies.return_value = mock_ethereum_treasury_response
        
        # Call the function
        result = get_companies_treasury(coin_id="ethereum", display=False)
        
        # Verify the result
        assert result is not None
        assert "total_holdings" in result
        assert result["total_holdings"] == 218306.0
        assert result["market_cap_dominance"] == 0.31
        assert len(result["companies"]) == 2
        
        # Check company data
        assert result["companies"][0]["name"] == "Galaxy Digital Holdings"
        assert result["companies"][1]["name"] == "Meitu Inc"
        
        # Verify the API was called with the correct coin ID
        mock_get_companies.assert_called_once_with("ethereum")

    @patch("app.companies.api.get_companies_public_treasury")
    def test_get_empty_treasury(self, mock_get_companies, mock_empty_treasury_response):
        """Test getting treasury data when no companies are found."""
        # Setup the mock to return empty data
        mock_get_companies.return_value = mock_empty_treasury_response
        
        # Call the function
        result = get_companies_treasury(coin_id="bitcoin", display=False)
        
        # Verify the result contains empty companies list
        assert result is not None
        assert "companies" in result
        assert len(result["companies"]) == 0
        assert result["total_holdings"] == 0
        assert result["total_value_usd"] == 0

    @patch("app.companies.api.get_companies_public_treasury")
    def test_get_treasury_api_error(self, mock_get_companies):
        """Test handling of API errors when getting treasury data."""
        # Setup the mock to raise an exception
        mock_get_companies.side_effect = Exception("API error")
        
        # Call the function
        result = get_companies_treasury(coin_id="bitcoin", display=False)
        
        # Verify the result is None due to the exception
        assert result is None
        mock_get_companies.assert_called_once_with("bitcoin")

    @patch("app.companies.api.get_companies_public_treasury")
    def test_save_treasury_data(self, mock_get_companies, mock_bitcoin_treasury_response):
        """Test saving treasury data to a file."""
        # Setup the mock to return test data
        mock_get_companies.return_value = mock_bitcoin_treasury_response
        
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_file = tmp.name
            
        try:
            # Call the function with save option
            result = get_companies_treasury(coin_id="bitcoin", display=False, save=True, output=tmp_file)
            
            # Verify the result
            assert result is not None
            assert os.path.exists(tmp_file)
            
            # Check the saved file content
            with open(tmp_file, "r") as f:
                saved_data = json.load(f)
                
            assert saved_data["total_holdings"] == 174045.0
            assert len(saved_data["companies"]) == 3
            assert saved_data["companies"][0]["name"] == "MicroStrategy"
        
        finally:
            # Clean up the temporary file
            if os.path.exists(tmp_file):
                os.remove(tmp_file)

    @patch("app.companies.console")
    @patch("app.companies.print_warning")
    def test_display_empty_treasury(self, mock_print_warning, mock_console, mock_empty_treasury_response):
        """Test display function with empty treasury data."""
        # Call the display function with empty data
        display_companies_treasury(mock_empty_treasury_response, "bitcoin")
        
        # Verify that warning was printed
        mock_print_warning.assert_called_once()
        assert "No public companies found" in mock_print_warning.call_args[0][0]

    @patch("app.companies.console")
    @patch("app.companies.Table")
    @patch("app.companies.Panel")
    def test_display_bitcoin_treasury(self, mock_panel, mock_table, mock_console, mock_bitcoin_treasury_response):
        """Test display function with Bitcoin treasury data."""
        # Setup mock table and panel
        table_instance = MagicMock()
        mock_table.return_value = table_instance
        panel_instance = MagicMock()
        mock_panel.return_value = panel_instance
        
        # Call the display function
        display_companies_treasury(mock_bitcoin_treasury_response, "bitcoin")
        
        # Verify that the table was created and contains correct columns
        mock_table.assert_called_once()
        column_names = [call.args[0] for call in table_instance.add_column.call_args_list]
        
        # Verify important columns are present
        assert "Company" in column_names
        assert "BTC Holdings" in column_names or "bitcoin Holdings" in column_names or "BITCOIN Holdings" in column_names
        assert "Entry Value (USD)" in column_names
        assert "Current Value (USD)" in column_names
        assert "% of Total Supply" in column_names
        
        # Verify correct number of rows added (3 companies in mock data)
        assert table_instance.add_row.call_count == 3
        
        # Verify console output was called
        assert mock_console.print.call_count >= 2

    @patch("app.companies.console")
    @patch("app.companies.Table")
    @patch("app.companies.Panel")
    def test_display_ethereum_treasury(self, mock_panel, mock_table, mock_console, mock_ethereum_treasury_response):
        """Test display function with Ethereum treasury data."""
        # Setup mock table and panel
        table_instance = MagicMock()
        mock_table.return_value = table_instance
        panel_instance = MagicMock()
        mock_panel.return_value = panel_instance
        
        # Call the display function
        display_companies_treasury(mock_ethereum_treasury_response, "ethereum")
        
        # Verify that the table was created with correct columns
        mock_table.assert_called_once()
        
        # Verify correct number of rows added (2 companies in Ethereum mock data)
        assert table_instance.add_row.call_count == 2
        
        # Verify console output was called
        assert mock_console.print.call_count >= 2

    def test_save_companies_treasury(self, mock_bitcoin_treasury_response):
        """Test the save function directly."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_file = tmp.name
            
        try:
            # Call the save function directly
            result_path = save_companies_treasury(mock_bitcoin_treasury_response, "bitcoin", tmp_file)
            
            # Verify the returned path
            assert result_path == os.path.abspath(tmp_file)
            assert os.path.exists(tmp_file)
            
            # Check file content
            with open(tmp_file, "r") as f:
                saved_data = json.load(f)
            
            assert saved_data == mock_bitcoin_treasury_response
            
        finally:
            # Clean up
            if os.path.exists(tmp_file):
                os.remove(tmp_file)

    def test_save_companies_treasury_default_filename(self, mock_ethereum_treasury_response):
        """Test the save function with default filename generation."""
        try:
            # Call the save function without a filename
            result_path = save_companies_treasury(mock_ethereum_treasury_response, "ethereum")
            
            # Verify the returned path exists and contains expected patterns
            assert os.path.exists(result_path)
            filename = os.path.basename(result_path)
            assert "companies" in filename
            assert "ethereum" in filename
            assert filename.endswith(".json")
            
            # Check file content
            with open(result_path, "r") as f:
                saved_data = json.load(f)
            
            assert saved_data == mock_ethereum_treasury_response
            
        finally:
            # Clean up
            if os.path.exists(result_path):
                os.remove(result_path)
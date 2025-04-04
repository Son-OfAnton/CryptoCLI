"""
Tests for the trending coins functionality.
"""
import pytest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
from app.trending import get_trending_coins, get_trending, display_trending_coins


class TestTrendingCoins:
    """Test cases for trending coins functionality."""

    @patch("app.trending.api.get_trending_coins")
    def test_get_trending_coins_success(self, mock_get_trending_coins, mock_trending_coins_response):
        """Test getting trending coins successfully."""
        # Setup the mock to return test data
        mock_get_trending_coins.return_value = mock_trending_coins_response

        # Call the function
        result = get_trending_coins(display=False)

        # Verify the result
        assert result is not None
        assert "coins" in result
        assert len(result["coins"]) == 3
        assert result["coins"][0]["item"]["name"] == "Bitcoin"
        assert result["coins"][1]["item"]["name"] == "Ethereum"
        assert result["coins"][2]["item"]["name"] == "Solana"

    @patch("app.trending.api.get_trending_coins")
    def test_get_trending_coins_empty(self, mock_get_trending_coins):
        """Test getting trending coins when API returns empty data."""
        # Setup the mock to return empty data
        mock_get_trending_coins.return_value = {"coins": []}

        # Call the function
        result = get_trending_coins(display=False)

        # Verify the result
        assert result is not None
        assert "coins" in result
        assert len(result["coins"]) == 0

    @patch("app.trending.api.get_trending_coins")
    def test_get_trending_coins_exception(self, mock_get_trending_coins):
        """Test handling of exceptions when getting trending coins."""
        # Setup the mock to raise an exception
        mock_get_trending_coins.side_effect = Exception("API error")

        # Call the function (should handle exception)
        result = get_trending_coins(display=False)

        # Verify the result is None due to the exception
        assert result is not None
        assert "coins" in result
        assert len(result["coins"]) == 0

    @patch("app.trending.api.get_trending_coins")
    def test_save_trending_coins(self, mock_get_trending_coins, mock_trending_coins_response):
        """Test saving trending coins data to a file."""
        # Setup the mock to return test data
        mock_get_trending_coins.return_value = mock_trending_coins_response

        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_file = tmp.name

        try:
            # Call the function with save option
            result = get_trending_coins(
                display=False, save=True, output=tmp_file)

            # Verify the result
            assert result is not None
            assert os.path.exists(tmp_file)

            # Check the saved file content
            with open(tmp_file, "r") as f:
                saved_data = json.load(f)

            assert "coins" in saved_data
            assert len(saved_data["coins"]) == 3
            assert saved_data["coins"][0]["item"]["name"] == "Bitcoin"

        finally:
            # Clean up the temporary file
            if os.path.exists(tmp_file):
                os.remove(tmp_file)

    @patch("app.trending.console")
    @patch("app.trending.print_warning")
    def test_display_trending_coins_empty(self, mock_print_warning, mock_console):
        """Test display function with empty data."""
        # Call the display function with empty data
        display_trending_coins({"coins": []})

        # Verify that warning was printed
        mock_print_warning.assert_called_once()
        assert "No trending coins found" in mock_print_warning.call_args[0][0]

    @patch("app.trending.console")
    @patch("app.trending.Table")
    def test_display_trending_coins(self, mock_table, mock_console, mock_trending_coins_response):
        """Test display function with valid data."""
        # Setup mock table
        table_instance = MagicMock()
        mock_table.return_value = table_instance

        # Call the display function
        display_trending_coins(mock_trending_coins_response)

        # Verify that the table was created and printed
        mock_table.assert_called_once()
        # At least 5 columns should be added
        assert table_instance.add_column.call_count >= 5
        assert table_instance.add_row.call_count == 3  # 3 rows for our test data
        mock_console.print.call_count >= 2  # Header and table


class TestMainTrendingCommand:
    """Test cases for the main trending command."""

    @patch("app.trending.api.get_trending_coins")
    @patch("app.trending.api.get_trending_nfts")
    def test_get_trending_coins_only(self, mock_get_nfts, mock_get_coins, mock_trending_coins_response):
        """Test get_trending with coins type."""
        # Setup mocks
        mock_get_coins.return_value = mock_trending_coins_response

        # Call the function with coins only
        result = get_trending(data_type="coins", display=False)

        # Verify the result
        assert result is not None
        assert "coins" in result
        assert len(result["coins"]) == 3

        # Verify that only trending coins API was called
        mock_get_coins.assert_called_once()
        mock_get_nfts.assert_not_called()

    @patch("app.trending.display_trending_coins")
    @patch("app.trending.display_trending_nfts")
    @patch("app.trending.api.get_trending_coins")
    def test_get_trending_display(self, mock_get_coins, mock_display_nfts, mock_display_coins,
                                  mock_trending_coins_response):
        """Test display functionality of get_trending."""
        # Setup mocks
        mock_get_coins.return_value = mock_trending_coins_response

        # Call the function with display=True
        get_trending(data_type="coins", display=True)

        # Verify display function was called correctly
        mock_display_coins.assert_called_once()
        mock_display_nfts.assert_not_called()

    @patch("app.trending.save_trending_data")
    @patch("app.trending.api.get_trending_coins")
    def test_get_trending_save(self, mock_get_coins, mock_save, mock_trending_coins_response):
        """Test save functionality of get_trending."""
        # Setup mocks
        mock_get_coins.return_value = mock_trending_coins_response
        mock_save.return_value = "/path/to/saved/file.json"

        # Call the function with save=True
        get_trending(data_type="coins", display=False,
                     save=True, output="test.json")

        # Verify save function was called correctly
        mock_save.assert_called_once_with({"coins": mock_trending_coins_response["coins"],
                                          "updated_at": mock_trending_coins_response["updated_at"]},
                                          "coins", "test.json")

"""
Combined tests for the search functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
import io
from rich.console import Console

from search import search_cryptocurrencies, display_search_results, get_cryptocurrency_suggestion

class TestSearchFunctionality:
    """Comprehensive test cases for cryptocurrency search functionality."""

    @pytest.fixture
    def mock_search_response(self):
        """Mock response for the CoinGecko search endpoint."""
        return {
            "coins": [
                {
                    "id": "bitcoin",
                    "name": "Bitcoin",
                    "symbol": "btc",
                    "market_cap_rank": 1,
                    "thumb": "https://assets.coingecko.com/coins/images/1/thumb/bitcoin.png",
                    "large": "https://assets.coingecko.com/coins/images/1/large/bitcoin.png"
                },
                {
                    "id": "bitcoin-cash",
                    "name": "Bitcoin Cash",
                    "symbol": "bch",
                    "market_cap_rank": 25,
                    "thumb": "https://assets.coingecko.com/coins/images/780/thumb/bitcoin-cash-circle.png",
                    "large": "https://assets.coingecko.com/coins/images/780/large/bitcoin-cash-circle.png"
                },
                {
                    "id": "bitcoin-gold",
                    "name": "Bitcoin Gold",
                    "symbol": "btg",
                    "market_cap_rank": 123,
                    "thumb": "https://assets.coingecko.com/coins/images/780/thumb/bitcoin-gold.png",
                    "large": "https://assets.coingecko.com/coins/images/780/large/bitcoin-gold.png"
                }
            ],
            "exchanges": [],
            "icos": [],
            "categories": []
        }

    @pytest.fixture
    def mock_ethereum_response(self):
        """Mock response for ethereum search."""
        return {
            "coins": [
                {
                    "id": "ethereum",
                    "name": "Ethereum",
                    "symbol": "eth",
                    "market_cap_rank": 2,
                    "thumb": "https://assets.coingecko.com/coins/images/279/thumb/ethereum.png",
                    "large": "https://assets.coingecko.com/coins/images/279/large/ethereum.png"
                },
                {
                    "id": "ethereum-classic",
                    "name": "Ethereum Classic",
                    "symbol": "etc",
                    "market_cap_rank": 27,
                    "thumb": "https://assets.coingecko.com/coins/images/453/thumb/ethereum-classic.png",
                    "large": "https://assets.coingecko.com/coins/images/453/large/ethereum-classic.png"
                }
            ],
            "exchanges": [],
            "icos": [],
            "categories": []
        }

    @pytest.fixture
    def mock_symbol_response(self):
        """Mock response for symbol search."""
        return {
            "coins": [
                {
                    "id": "solana",
                    "name": "Solana",
                    "symbol": "sol",
                    "market_cap_rank": 5,
                    "thumb": "https://assets.coingecko.com/coins/images/4128/thumb/solana.png",
                    "large": "https://assets.coingecko.com/coins/images/4128/large/solana.png"
                }
            ],
            "exchanges": [],
            "icos": [],
            "categories": []
        }

    def test_search_by_name(self, mock_api, mock_ethereum_response):
        """
        Test searching by cryptocurrency name.
        Should return results that match the name.
        """
        # Setup the mock API to return our test data
        mock_api.search_coins.return_value = mock_ethereum_response
        
        # Create a string buffer to capture console output
        console_output = io.StringIO()
        test_console = Console(file=console_output)
        
        # Patch the API instance and console
        with patch('CryptoCLI.search.api', mock_api):
            with patch('CryptoCLI.search.console', test_console):
                # Call with a name search query
                result = search_cryptocurrencies("Ethereum")
                
                # Check the API was called with the correct parameters
                mock_api.search_coins.assert_called_once_with("Ethereum")
                
                # Verify the result structure
                assert result["query"] == "Ethereum"
                assert result["total_results"] == 2
                assert result["displayed_results"] == 2
                assert len(result["coins"]) == 2
                assert result["coins"][0]["id"] == "ethereum"
                assert result["coins"][1]["id"] == "ethereum-classic"
                
                # Check the output contains the expected values
                output = console_output.getvalue()
                assert "Ethereum" in output
                assert "ETH" in output
                assert "Ethereum Classic" in output
                assert "ETC" in output
                assert "#2" in output  # market cap rank for Ethereum
                assert "#27" in output  # market cap rank for Ethereum Classic

    def test_search_by_symbol(self, mock_api, mock_symbol_response):
        """
        Test searching by cryptocurrency symbol.
        Should return results that match the symbol.
        """
        # Setup the mock API to return our test data
        mock_api.search_coins.return_value = mock_symbol_response
        
        # Create a string buffer to capture console output
        console_output = io.StringIO()
        test_console = Console(file=console_output)
        
        # Patch the API instance and console
        with patch('CryptoCLI.search.api', mock_api):
            with patch('CryptoCLI.search.console', test_console):
                # Call with a symbol search query
                result = search_cryptocurrencies("sol")
                
                # Check the API was called with the correct parameters
                mock_api.search_coins.assert_called_once_with("sol")
                
                # Verify the result structure
                assert result["query"] == "sol"
                assert result["total_results"] == 1
                assert result["displayed_results"] == 1
                assert len(result["coins"]) == 1
                assert result["coins"][0]["id"] == "solana"
                assert result["coins"][0]["symbol"] == "sol"
                
                # Check the output contains the expected values
                output = console_output.getvalue()
                assert "Solana" in output
                assert "SOL" in output
                assert "#5" in output  # market cap rank

    def test_search_with_partial_name(self, mock_api, mock_search_response):
        """
        Test searching with a partial name.
        Should return all results containing the partial name.
        """
        # Setup the mock API to return our test data
        mock_api.search_coins.return_value = mock_search_response
        
        # Create a string buffer to capture console output
        console_output = io.StringIO()
        test_console = Console(file=console_output)
        
        # Patch the API instance and console
        with patch('CryptoCLI.search.api', mock_api):
            with patch('CryptoCLI.search.console', test_console):
                # Call with a partial name search query
                result = search_cryptocurrencies("bit")
                
                # Check the API was called with the correct parameters
                mock_api.search_coins.assert_called_once_with("bit")
                
                # Verify the result structure
                assert result["query"] == "bit"
                assert result["total_results"] == 3
                assert result["displayed_results"] == 3
                assert len(result["coins"]) == 3
                
                # Check all coins containing "bit" are returned
                coin_ids = [coin["id"] for coin in result["coins"]]
                assert "bitcoin" in coin_ids
                assert "bitcoin-cash" in coin_ids
                assert "bitcoin-gold" in coin_ids
                
                # Check the output contains all expected coins
                output = console_output.getvalue()
                assert "Bitcoin" in output
                assert "BTC" in output
                assert "Bitcoin Cash" in output
                assert "BCH" in output
                assert "Bitcoin Gold" in output
                assert "BTG" in output

    def test_case_insensitive_search(self, mock_api, mock_search_response):
        """
        Test case-insensitive searching.
        Should return results regardless of case.
        """
        # Setup the mock API to return our test data
        mock_api.search_coins.return_value = mock_search_response
        
        # List of different case variations to test
        case_variations = ["bitcoin", "BITCOIN", "Bitcoin", "BitCoin", "bitCOIN"]
        
        for query in case_variations:
            # Reset the mock
            mock_api.reset_mock()
            
            # Create a string buffer to capture console output
            console_output = io.StringIO()
            test_console = Console(file=console_output)
            
            # Patch the API instance and console
            with patch('CryptoCLI.search.api', mock_api):
                with patch('CryptoCLI.search.console', test_console):
                    # Call with the case-varied query
                    result = search_cryptocurrencies(query)
                    
                    # Check the API was called with the exact case provided
                    mock_api.search_coins.assert_called_once_with(query)
                    
                    # All variations should return the same results
                    assert result["total_results"] == 3
                    assert "bitcoin" in [coin["id"] for coin in result["coins"]]
                    
                    # Check the output contains Bitcoin
                    output = console_output.getvalue()
                    assert "Bitcoin" in output

    def test_limit_results(self, mock_api, mock_search_response):
        """
        Test limiting the number of search results.
        Should return only the specified number of results.
        """
        # Setup the mock API to return our test data
        mock_api.search_coins.return_value = mock_search_response
        
        # Create a string buffer to capture console output
        console_output = io.StringIO()
        test_console = Console(file=console_output)
        
        # Patch the API instance and console
        with patch('CryptoCLI.search.api', mock_api):
            with patch('CryptoCLI.search.console', test_console):
                # Call with a limit of 2
                result = search_cryptocurrencies("bitcoin", limit=2)
                
                # Check the API was called with the correct parameters
                mock_api.search_coins.assert_called_once_with("bitcoin")
                
                # Verify the result is limited
                assert result["total_results"] == 3  # Total available is 3
                assert result["displayed_results"] == 2  # But we display only 2
                assert len(result["coins"]) == 2
                
                # Check only the first 2 results are included
                assert result["coins"][0]["id"] == "bitcoin"
                assert result["coins"][1]["id"] == "bitcoin-cash"
                assert not any(coin["id"] == "bitcoin-gold" for coin in result["coins"])
                
                # Check the output
                output = console_output.getvalue()
                assert "Bitcoin" in output
                assert "Bitcoin Cash" in output
                assert "Bitcoin Gold" not in output

    def test_get_suggestion_functionality(self, mock_api, mock_search_response, mock_ethereum_response, mock_symbol_response):
        """
        Test the get_cryptocurrency_suggestion function.
        Should return the best match for different cryptocurrency searches.
        """
        # Setup a side_effect to return different responses based on the query
        def mock_search_side_effect(query):
            if "bit" in query.lower():
                return mock_search_response
            elif "eth" in query.lower():
                return mock_ethereum_response
            elif "sol" in query.lower():
                return mock_symbol_response
            else:
                return {"coins": []}
        
        mock_api.search_coins.side_effect = mock_search_side_effect
        
        # Patch the API instance
        with patch('CryptoCLI.search.api', mock_api):
            # Test various queries
            
            # Full name
            assert get_cryptocurrency_suggestion("bitcoin") == "bitcoin"
            
            # Partial name
            assert get_cryptocurrency_suggestion("bit") == "bitcoin"
            
            # Symbol
            assert get_cryptocurrency_suggestion("eth") == "ethereum"
            
            # Full name of another coin
            assert get_cryptocurrency_suggestion("solana") == "solana"
            
            # Symbol of another coin
            assert get_cryptocurrency_suggestion("sol") == "solana"
            
            # Non-existent coin
            assert get_cryptocurrency_suggestion("nonexistentcoin") is None

    def test_cli_search_integration(self, monkeypatch):
        """
        Test the search command integration with the CLI.
        Should properly pass arguments to the search function.
        """
        from click.testing import CliRunner
        from main import search
        
        # Create multiple mock functions for different scenarios
        mock_search_by_name = MagicMock()
        mock_search_by_symbol = MagicMock()
        mock_search_with_limit = MagicMock()
        
        # Patch the search function for each test case
        with patch('CryptoCLI.main.search_cryptocurrencies', mock_search_by_name):
            runner = CliRunner()
            result = runner.invoke(search, ['ethereum'])
            
            # Check for successful execution
            assert result.exit_code == 0
            
            # Verify the function was called with the correct arguments
            mock_search_by_name.assert_called_once_with('ethereum', limit=10)
        
        # Test searching by symbol
        with patch('CryptoCLI.main.search_cryptocurrencies', mock_search_by_symbol):
            runner = CliRunner()
            result = runner.invoke(search, ['btc'])
            
            # Check for successful execution
            assert result.exit_code == 0
            
            # Verify the function was called with the correct arguments
            mock_search_by_symbol.assert_called_once_with('btc', limit=10)
        
        # Test with custom limit
        with patch('CryptoCLI.main.search_cryptocurrencies', mock_search_with_limit):
            runner = CliRunner()
            result = runner.invoke(search, ['dog', '--limit', '5'])
            
            # Check for successful execution
            assert result.exit_code == 0
            
            # Verify the function was called with the correct arguments
            mock_search_with_limit.assert_called_once_with('dog', limit=5)

    def test_error_handling_and_feedback(self, mock_api, mock_search_response):
        """
        Test error handling and user feedback.
        Should provide clear feedback for different scenarios.
        """
        # Setup the mock API with different responses for different cases
        mock_api.search_coins.side_effect = [
            mock_search_response,                # Normal response
            {"coins": []},                       # Empty response
            Exception("API request failed")      # Error response
        ]
        
        # Test normal response (already tested in other tests)
        # Test empty response
        console_output = io.StringIO()
        test_console = Console(file=console_output)
        
        with patch('CryptoCLI.search.api', mock_api):
            with patch('CryptoCLI.search.console', test_console):
                # Call with a query that will return no results
                result = search_cryptocurrencies("nonexistentcoin")
                
                # Check for warning message
                output = console_output.getvalue()
                assert "Warning" in output
                assert "No cryptocurrencies found" in output
        
        # Test error response
        console_output = io.StringIO()
        test_console = Console(file=console_output)
        
        with patch('CryptoCLI.search.api', mock_api):
            with patch('CryptoCLI.search.console', test_console):
                # Call with a query that will cause an API error
                result = search_cryptocurrencies("error")
                
                # Check for error message
                output = console_output.getvalue()
                assert "Error" in output
                assert "Failed to search" in output

if __name__ == "__main__":
    pytest.main(["-v", "test_search_combined.py"])
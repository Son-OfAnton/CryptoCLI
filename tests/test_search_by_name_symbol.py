"""
Specific tests for searching cryptocurrencies by name or symbol.
"""
import pytest
from unittest.mock import patch, MagicMock
import io
from rich.console import Console

from search import search_cryptocurrencies, display_search_results

class TestSearchByNameOrSymbol:
    """Test cases specifically for searching cryptocurrencies by name or symbol."""

    @pytest.fixture
    def mock_search_by_name_response(self):
        """Mock response for searching by cryptocurrency name."""
        return {
            "coins": [
                {
                    "id": "ethereum",
                    "name": "Ethereum",
                    "symbol": "eth",
                    "market_cap_rank": 2
                },
                {
                    "id": "ethereum-classic",
                    "name": "Ethereum Classic",
                    "symbol": "etc",
                    "market_cap_rank": 27
                },
                {
                    "id": "ethereum-pow-iou",
                    "name": "EthereumPoW",
                    "symbol": "ethw",
                    "market_cap_rank": 76
                }
            ],
            "exchanges": [],
            "icos": [],
            "categories": []
        }
    
    @pytest.fixture
    def mock_search_by_symbol_response(self):
        """Mock response for searching by cryptocurrency symbol."""
        return {
            "coins": [
                {
                    "id": "solana",
                    "name": "Solana",
                    "symbol": "sol",
                    "market_cap_rank": 5
                },
                {
                    "id": "solve",
                    "name": "SOLVE",
                    "symbol": "solve",
                    "market_cap_rank": 672
                },
                {
                    "id": "sol-token",
                    "name": "SOL Token",
                    "symbol": "sol",
                    "market_cap_rank": 1204
                }
            ],
            "exchanges": [],
            "icos": [],
            "categories": []
        }
    
    @pytest.fixture
    def mock_search_exact_match_response(self):
        """Mock response for searching with an exact match."""
        return {
            "coins": [
                {
                    "id": "bitcoin",
                    "name": "Bitcoin",
                    "symbol": "btc",
                    "market_cap_rank": 1
                }
            ],
            "exchanges": [],
            "icos": [],
            "categories": []
        }
    
    @pytest.fixture
    def mock_search_partial_match_response(self):
        """Mock response for searching with a partial match."""
        return {
            "coins": [
                {
                    "id": "cardano",
                    "name": "Cardano",
                    "symbol": "ada",
                    "market_cap_rank": 8
                },
                {
                    "id": "adacash",
                    "name": "ADAcash",
                    "symbol": "adac",
                    "market_cap_rank": None
                },
                {
                    "id": "cardence",
                    "name": "Cardence",
                    "symbol": "crdn",
                    "market_cap_rank": 2517
                }
            ],
            "exchanges": [],
            "icos": [],
            "categories": []
        }
    
    @pytest.fixture
    def mock_search_mixed_case_response(self):
        """Mock response for searching with mixed case."""
        return {
            "coins": [
                {
                    "id": "polkadot",
                    "name": "Polkadot",
                    "symbol": "dot",
                    "market_cap_rank": 11
                },
                {
                    "id": "polka-city",
                    "name": "Polka City",
                    "symbol": "polc",
                    "market_cap_rank": None
                }
            ],
            "exchanges": [],
            "icos": [],
            "categories": []
        }
    
    def test_search_by_full_name(self, mock_api, mock_search_by_name_response):
        """
        Test searching by full cryptocurrency name.
        Should return results that match the full name.
        """
        # Setup the mock API to return our test data
        mock_api.search_coins.return_value = mock_search_by_name_response
        
        # Create a string buffer to capture console output
        console_output = io.StringIO()
        test_console = Console(file=console_output)
        
        # Patch the API instance and console
        with patch('CryptoCLI.search.api', mock_api):
            with patch('CryptoCLI.search.console', test_console):
                # Call with a full name search query
                result = search_cryptocurrencies("Ethereum")
                
                # Check the API was called with the correct parameters
                mock_api.search_coins.assert_called_once_with("Ethereum")
                
                # Verify the result structure
                assert result["query"] == "Ethereum"
                assert result["total_results"] == 3
                assert result["displayed_results"] == 3
                assert len(result["coins"]) == 3
                
                # Check the output contains the expected values
                output = console_output.getvalue()
                assert "Ethereum" in output
                assert "ETH" in output
                assert "Ethereum Classic" in output
                assert "ETC" in output
                assert "EthereumPoW" in output
                assert "ETHW" in output
    
    def test_search_by_symbol(self, mock_api, mock_search_by_symbol_response):
        """
        Test searching by cryptocurrency symbol.
        Should return results that match the symbol.
        """
        # Setup the mock API to return our test data
        mock_api.search_coins.return_value = mock_search_by_symbol_response
        
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
                assert result["total_results"] == 3
                assert result["displayed_results"] == 3
                assert len(result["coins"]) == 3
                
                # Check the output contains the expected values
                output = console_output.getvalue()
                assert "Solana" in output
                assert "SOL" in output
                assert "SOLVE" in output
                assert "SOL Token" in output
    
    def test_search_exact_match(self, mock_api, mock_search_exact_match_response):
        """
        Test searching with exact match.
        Should return only the exact match.
        """
        # Setup the mock API to return our test data
        mock_api.search_coins.return_value = mock_search_exact_match_response
        
        # Create a string buffer to capture console output
        console_output = io.StringIO()
        test_console = Console(file=console_output)
        
        # Patch the API instance and console
        with patch('CryptoCLI.search.api', mock_api):
            with patch('CryptoCLI.search.console', test_console):
                # Call with an exact match search query
                result = search_cryptocurrencies("bitcoin")
                
                # Check the API was called with the correct parameters
                mock_api.search_coins.assert_called_once_with("bitcoin")
                
                # Verify the result structure
                assert result["query"] == "bitcoin"
                assert result["total_results"] == 1
                assert result["displayed_results"] == 1
                assert len(result["coins"]) == 1
                assert result["coins"][0]["id"] == "bitcoin"
                
                # Check the output contains the expected values
                output = console_output.getvalue()
                assert "Bitcoin" in output
                assert "BTC" in output
                assert "#1" in output  # market cap rank
    
    def test_search_partial_name(self, mock_api, mock_search_partial_match_response):
        """
        Test searching by partial cryptocurrency name.
        Should return results that partially match the name.
        """
        # Setup the mock API to return our test data
        mock_api.search_coins.return_value = mock_search_partial_match_response
        
        # Create a string buffer to capture console output
        console_output = io.StringIO()
        test_console = Console(file=console_output)
        
        # Patch the API instance and console
        with patch('CryptoCLI.search.api', mock_api):
            with patch('CryptoCLI.search.console', test_console):
                # Call with a partial name search query
                result = search_cryptocurrencies("card")
                
                # Check the API was called with the correct parameters
                mock_api.search_coins.assert_called_once_with("card")
                
                # Verify the result structure
                assert result["query"] == "card"
                assert result["total_results"] == 3
                assert result["displayed_results"] == 3
                assert len(result["coins"]) == 3
                
                # Check the output contains the expected values
                output = console_output.getvalue()
                assert "Cardano" in output
                assert "ADA" in output
                assert "Cardence" in output
                assert "CRDN" in output
                assert "ADAcash" in output
                assert "ADAC" in output
    
    def test_search_case_insensitivity(self, mock_api, mock_search_mixed_case_response):
        """
        Test case insensitivity in search.
        Should handle mixed case queries correctly.
        """
        # Setup the mock API to return our test data
        mock_api.search_coins.return_value = mock_search_mixed_case_response
        
        # Create a string buffer to capture console output
        console_output = io.StringIO()
        test_console = Console(file=console_output)
        
        # Patch the API instance and console
        with patch('CryptoCLI.search.api', mock_api):
            with patch('CryptoCLI.search.console', test_console):
                # Call with a mixed case search query
                result = search_cryptocurrencies("PoLkAdOt")
                
                # Check the API was called with the correct parameters
                mock_api.search_coins.assert_called_once_with("PoLkAdOt")
                
                # Verify the result structure
                assert result["query"] == "PoLkAdOt"
                assert result["total_results"] == 2
                assert result["displayed_results"] == 2
                assert len(result["coins"]) == 2
                
                # Check the output contains the expected values
                output = console_output.getvalue()
                assert "Polkadot" in output
                assert "DOT" in output
                assert "Polka City" in output
                assert "POLC" in output
    
    def test_symbol_and_name_suggestions(self, mock_api):
        """
        Test that the search function provides appropriate suggestions.
        """
        # Create test responses for different queries
        btc_response = {
            "coins": [
                {"id": "bitcoin", "name": "Bitcoin", "symbol": "btc", "market_cap_rank": 1}
            ]
        }
        
        eth_response = {
            "coins": [
                {"id": "ethereum", "name": "Ethereum", "symbol": "eth", "market_cap_rank": 2}
            ]
        }
        
        # Setup the mock API to return different responses based on the search query
        mock_api.search_coins = MagicMock(side_effect=lambda query: 
            btc_response if query.lower() == "btc" else 
            eth_response if query.lower() == "eth" else 
            {"coins": []}
        )
        
        # Create a string buffer to capture console output
        console_output = io.StringIO()
        test_console = Console(file=console_output)
        
        # Patch the API instance and console
        with patch('CryptoCLI.search.api', mock_api):
            with patch('CryptoCLI.search.console', test_console):
                # Test searching by symbol "btc"
                result1 = search_cryptocurrencies("btc")
                assert result1["coins"][0]["id"] == "bitcoin"
                
                # Clear the output buffer
                console_output.truncate(0)
                console_output.seek(0)
                
                # Test searching by symbol "eth"
                result2 = search_cryptocurrencies("eth")
                assert result2["coins"][0]["id"] == "ethereum"
                
                # Verify the API was called with the correct parameters each time
                assert mock_api.search_coins.call_count == 2
                mock_api.search_coins.assert_any_call("btc")
                mock_api.search_coins.assert_any_call("eth")
    
    def test_search_display_format_consistency(self, mock_api, mock_search_by_name_response, mock_search_by_symbol_response):
        """
        Test that the display format is consistent regardless of search type.
        """
        # Create string buffers to capture console output
        name_output = io.StringIO()
        symbol_output = io.StringIO()
        name_console = Console(file=name_output)
        symbol_console = Console(file=symbol_output)
        
        # Patch for name search
        mock_api.search_coins.return_value = mock_search_by_name_response
        with patch('CryptoCLI.search.api', mock_api):
            with patch('CryptoCLI.search.console', name_console):
                search_cryptocurrencies("Ethereum")
        
        # Patch for symbol search
        mock_api.search_coins.return_value = mock_search_by_symbol_response
        with patch('CryptoCLI.search.api', mock_api):
            with patch('CryptoCLI.search.console', symbol_console):
                search_cryptocurrencies("sol")
        
        # Get outputs
        name_text = name_output.getvalue()
        symbol_text = symbol_output.getvalue()
        
        # Check that both outputs have the same table structure
        assert "Cryptocurrency Search Results" in name_text
        assert "Cryptocurrency Search Results" in symbol_text
        assert "Rank" in name_text and "Rank" in symbol_text
        assert "ID" in name_text and "ID" in symbol_text
        assert "Name" in name_text and "Name" in symbol_text
        assert "Symbol" in name_text and "Symbol" in symbol_text
        assert "Market Cap Rank" in name_text and "Market Cap Rank" in symbol_text
        
        # Check that both show the usage examples
        assert "Use the ID in the second column with other commands" in name_text
        assert "Use the ID in the second column with other commands" in symbol_text

if __name__ == "__main__":
    pytest.main(["-v", "test_search_by_name_symbol.py"])
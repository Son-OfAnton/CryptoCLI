"""
Tests for the exchange_volume module which provides exchange volume history by date range.
"""
import pytest
from unittest.mock import patch, MagicMock
import json
from io import StringIO
import sys
import time
from datetime import datetime, timedelta

from app.exchange_volume import (
    get_exchange_volume_history,
    get_exchange_info,
    display_exchange_volume,
    display_volume_chart,
    save_exchange_volume_data,
    convert_date_to_timestamp,
    analyze_volume_trends
)


@pytest.fixture
def mock_exchange_info_response():
    """Mock response for exchange info"""
    return {
        "id": "binance",
        "name": "Binance",
        "year_established": 2017,
        "country": "Cayman Islands",
        "description": "Binance is a global cryptocurrency exchange that provides a platform for trading more than 100 cryptocurrencies.",
        "url": "https://www.binance.com/",
        "image": "https://assets.coingecko.com/markets/images/52/small/binance.jpg",
        "has_trading_incentive": False,
        "trust_score": 10,
        "trust_score_rank": 1,
        "trade_volume_24h_btc": 100000.0,
        "trade_volume_24h_btc_normalized": 100000.0
    }


@pytest.fixture
def mock_exchanges_response():
    """Mock response for exchanges endpoint"""
    return [
        {
            "id": "binance",
            "name": "Binance",
            "year_established": 2017,
            "country": "Cayman Islands",
            "description": "Binance is a global cryptocurrency exchange that provides a platform for trading more than 100 cryptocurrencies.",
            "url": "https://www.binance.com/",
            "image": "https://assets.coingecko.com/markets/images/52/small/binance.jpg",
            "has_trading_incentive": False,
            "trust_score": 10,
            "trust_score_rank": 1,
            "trade_volume_24h_btc": 100000.0,
            "trade_volume_24h_btc_normalized": 100000.0
        },
        {
            "id": "gdax",
            "name": "Coinbase Exchange",
            "year_established": 2012,
            "country": "United States",
            "description": "Coinbase Exchange is a digital currency exchange headquartered in San Francisco, California.",
            "url": "https://www.coinbase.com/",
            "image": "https://assets.coingecko.com/markets/images/23/small/Coinbase_Coin_Primary.png",
            "has_trading_incentive": False,
            "trust_score": 10,
            "trust_score_rank": 2,
            "trade_volume_24h_btc": 50000.0,
            "trade_volume_24h_btc_normalized": 50000.0
        },
        {
            "id": "kraken",
            "name": "Kraken",
            "year_established": 2011,
            "country": "United States",
            "description": "Kraken is a cryptocurrency exchange operating in Canada, the EU, Japan, and the US.",
            "url": "https://www.kraken.com/",
            "image": "https://assets.coingecko.com/markets/images/29/small/kraken.jpg",
            "has_trading_incentive": False,
            "trust_score": 10,
            "trust_score_rank": 3,
            "trade_volume_24h_btc": 40000.0,
            "trade_volume_24h_btc_normalized": 40000.0
        }
    ]


@pytest.fixture
def mock_volume_chart_data():
    """Mock response for exchange volume chart data"""
    # Generate 30 days of volume data, with timestamps in milliseconds
    now = datetime.now()
    data = []
    
    for i in range(30):
        day = now - timedelta(days=i)
        timestamp = int(day.timestamp() * 1000)  # Convert to milliseconds
        volume = 5000 + (i % 7) * 1000  # Some variation in volume
        data.append([timestamp, volume])
    
    # Sort by timestamp (oldest first)
    data.sort(key=lambda x: x[0])
    
    return data


@pytest.fixture
def mock_volume_result(mock_exchange_info_response, mock_volume_chart_data):
    """Mock result from get_exchange_volume_history"""
    # Get timestamps for a 30-day period
    now = int(time.time())
    from_timestamp = now - (30 * 86400)  # 30 days ago
    
    volume_values = [entry[1] for entry in mock_volume_chart_data]
    
    return {
        "exchange_id": mock_exchange_info_response["id"],
        "exchange_name": mock_exchange_info_response["name"],
        "from_timestamp": from_timestamp,
        "to_timestamp": now,
        "volume_data": mock_volume_chart_data,
        "success": True,
        "timestamp": now,
        "statistics": {
            "total_volume": sum(volume_values),
            "avg_daily_volume": sum(volume_values) / len(volume_values) if volume_values else 0,
            "max_volume": max(volume_values) if volume_values else 0,
            "min_volume": min(volume_values) if volume_values else 0,
            "data_points": len(mock_volume_chart_data)
        },
        "volume_change": {
            "absolute": mock_volume_chart_data[-1][1] - mock_volume_chart_data[0][1],
            "percentage": ((mock_volume_chart_data[-1][1] - mock_volume_chart_data[0][1]) / mock_volume_chart_data[0][1]) * 100
        }
    }


@pytest.fixture
def capture_stdout():
    """Fixture to capture stdout for testing console output"""
    stdout = StringIO()
    old_stdout = sys.stdout
    sys.stdout = stdout
    yield stdout
    sys.stdout = old_stdout


class TestExchangeVolume:
    """Test suite for exchange volume functionality"""
    
    @patch('app.exchange_volume.api')
    @patch('app.exchange_volume.get_exchange_info')
    @patch('app.exchange_volume.display_exchange_volume')
    @patch('app.exchange_volume.display_volume_chart')
    def test_get_exchange_volume_history(self, mock_display_chart, mock_display, mock_get_info, mock_api, mock_exchange_info_response, mock_volume_chart_data):
        """Test getting exchange volume history"""
        # Setup mocks
        mock_get_info.return_value = mock_exchange_info_response
        mock_api.get_exchange_volume_chart.return_value = mock_volume_chart_data
        
        # Call function with explicit UNIX timestamps
        now = int(time.time())
        from_timestamp = now - (10 * 86400)  # 10 days ago
        
        result = get_exchange_volume_history(
            exchange_id="binance",
            from_timestamp=from_timestamp,
            to_timestamp=now,
            display=True
        )
        
        # Verify API call
        mock_api.get_exchange_volume_chart.assert_called_once()
        mock_get_info.assert_called_with("binance")
        
        # Verify result structure
        assert result["exchange_id"] == "binance"
        assert result["exchange_name"] == "Binance"
        assert result["from_timestamp"] == from_timestamp
        assert result["to_timestamp"] == now
        assert result["success"] is True
        assert "volume_data" in result
        assert "statistics" in result
        assert "volume_change" in result
        
        # Verify display functions were called
        mock_display.assert_called_once_with(result)
        mock_display_chart.assert_called_once_with(result)
    
    @patch('app.exchange_volume.api')
    def test_get_exchange_info(self, mock_api, mock_exchanges_response):
        """Test getting exchange info"""
        # Setup mock
        mock_api.get_exchanges.return_value = mock_exchanges_response
        
        # Test finding existing exchange
        result = get_exchange_info("binance")
        assert result["id"] == "binance"
        assert result["name"] == "Binance"
        
        # Test another exchange
        result = get_exchange_info("kraken")
        assert result["id"] == "kraken"
        assert result["name"] == "Kraken"
        
        # Test with non-existent exchange
        result = get_exchange_info("nonexistent")
        assert result == {}
        
        # Verify API call
        mock_api.get_exchanges.assert_called()
    
    @patch('app.exchange_volume.api')
    @patch('app.exchange_volume.get_exchange_info')
    def test_get_exchange_volume_history_invalid_exchange(self, mock_get_info, mock_api):
        """Test error handling for invalid exchange ID"""
        # Setup mocks
        mock_get_info.return_value = {}  # Empty response means exchange not found
        
        # Call function
        now = int(time.time())
        from_timestamp = now - (10 * 86400)
        
        result = get_exchange_volume_history(
            exchange_id="nonexistent",
            from_timestamp=from_timestamp,
            to_timestamp=now,
            display=False
        )
        
        # Verify error handling
        assert result["success"] is False
        assert "Exchange not found" in result["error"]
        assert result["exchange_name"] is None
        
        # Verify API wasn't called for volume data
        mock_api.get_exchange_volume_chart.assert_not_called()
    
    @patch('app.exchange_volume.api')
    @patch('app.exchange_volume.get_exchange_info')
    def test_get_exchange_volume_history_api_error(self, mock_get_info, mock_api, mock_exchange_info_response):
        """Test error handling for API error"""
        # Setup mocks
        mock_get_info.return_value = mock_exchange_info_response
        mock_api.get_exchange_volume_chart.side_effect = Exception("API error")
        
        # Call function
        now = int(time.time())
        from_timestamp = now - (10 * 86400)
        
        result = get_exchange_volume_history(
            exchange_id="binance",
            from_timestamp=from_timestamp,
            to_timestamp=now,
            display=False
        )
        
        # Verify error handling
        assert result["success"] is False
        assert "API error" in result["error"]
    
    @patch('app.exchange_volume.api')
    @patch('app.exchange_volume.get_exchange_info')
    def test_get_exchange_volume_history_date_filtering(self, mock_get_info, mock_api, mock_exchange_info_response, mock_volume_chart_data):
        """Test filtering volume data by date range"""
        # Setup mocks
        mock_get_info.return_value = mock_exchange_info_response
        mock_api.get_exchange_volume_chart.return_value = mock_volume_chart_data
        
        # Use specific timestamps that should filter out some data points
        # Generate timestamps that will include only a portion of the mock data
        oldest_timestamp_ms = min(entry[0] for entry in mock_volume_chart_data)
        newest_timestamp_ms = max(entry[0] for entry in mock_volume_chart_data)
        
        # Convert to seconds for the API function
        oldest_timestamp = oldest_timestamp_ms // 1000
        newest_timestamp = newest_timestamp_ms // 1000
        
        # Use a date range that should include about half the data points
        mid_point = oldest_timestamp + (newest_timestamp - oldest_timestamp) // 2
        
        # Call function with range that should filter some points
        result = get_exchange_volume_history(
            exchange_id="binance",
            from_timestamp=mid_point,
            to_timestamp=newest_timestamp,
            display=False
        )
        
        # Verify that filtering took place
        assert len(result["volume_data"]) < len(mock_volume_chart_data)
        
        # Verify all included points are within the specified range
        for timestamp, _ in result["volume_data"]:
            timestamp_seconds = timestamp // 1000
            assert mid_point <= timestamp_seconds <= newest_timestamp
    
    @patch('app.exchange_volume.api')
    @patch('app.exchange_volume.get_exchange_info')
    def test_get_exchange_volume_history_invalid_date_range(self, mock_get_info, mock_api, mock_exchange_info_response, mock_volume_chart_data):
        """Test handling of invalid date ranges"""
        # Setup mocks
        mock_get_info.return_value = mock_exchange_info_response
        mock_api.get_exchange_volume_chart.return_value = mock_volume_chart_data
        
        # Call with to_timestamp before from_timestamp (invalid)
        now = int(time.time())
        from_timestamp = now - (5 * 86400)
        
        # Swapping timestamps to create invalid range
        result = get_exchange_volume_history(
            exchange_id="binance",
            from_timestamp=now,        # Later timestamp
            to_timestamp=from_timestamp,  # Earlier timestamp
            display=False
        )
        
        # API should still be called, but filtering will result in empty data
        assert mock_api.get_exchange_volume_chart.called
        assert len(result["volume_data"]) == 0
        assert result["statistics"]["data_points"] == 0
    
    def test_display_exchange_volume(self, mock_volume_result, capture_stdout):
        """Test displaying exchange volume data"""
        # Call function
        display_exchange_volume(mock_volume_result)
        
        # Check output
        output = capture_stdout.getvalue()
        assert "Binance" in output
        assert "Volume Statistics" in output
        assert "Total Volume" in output
        assert "Average Daily Volume" in output
        assert "Maximum Volume" in output
        assert "Minimum Volume" in output
        assert "Volume Change" in output
        assert "Volume Data Sample" in output
    
    def test_display_volume_chart(self, mock_volume_result, capture_stdout):
        """Test displaying volume chart"""
        # Call function
        display_volume_chart(mock_volume_result)
        
        # Check output
        output = capture_stdout.getvalue()
        assert "Volume Chart for Binance" in output
        assert "Max:" in output
        assert "Min:" in output
    
    def test_save_exchange_volume_data(self, mock_volume_result, tmpdir):
        """Test saving exchange volume data"""
        # Save to a temp file
        temp_file = tmpdir.join("volume_data.json")
        output_path = save_exchange_volume_data(mock_volume_result, str(temp_file))
        
        # Verify the file was saved
        assert output_path == str(temp_file)
        assert temp_file.exists()
        
        # Verify file contents
        saved_data = json.loads(temp_file.read())
        assert saved_data["exchange_id"] == "binance"
        assert saved_data["exchange_name"] == "Binance"
        assert "volume_data" in saved_data
        assert "statistics" in saved_data
    
    def test_save_exchange_volume_data_default_filename(self, mock_volume_result, tmpdir, monkeypatch):
        """Test saving with default filename"""
        # Change to temp directory
        monkeypatch.chdir(tmpdir)
        
        # Save with default filename
        output_path = save_exchange_volume_data(mock_volume_result)
        
        # Verify the file was created
        assert output_path.startswith("binance_volume_")
        assert output_path.endswith(".json")
        assert tmpdir.join(output_path).exists()
    
    def test_convert_date_to_timestamp(self):
        """Test date string to timestamp conversion"""
        # Test valid date
        timestamp = convert_date_to_timestamp("2023-01-01")
        expected = int(datetime(2023, 1, 1).timestamp())
        assert timestamp == expected
        
        # Test current date
        today = datetime.now().strftime('%Y-%m-%d')
        timestamp = convert_date_to_timestamp(today)
        expected = int(datetime.strptime(today, '%Y-%m-%d').timestamp())
        assert timestamp == expected
        
        # Test invalid date format
        timestamp = convert_date_to_timestamp("01/01/2023")
        assert timestamp == 0
    
    def test_analyze_volume_trends(self, mock_volume_result):
        """Test volume trend analysis"""
        # Call function
        analysis = analyze_volume_trends(mock_volume_result)
        
        # Verify analysis structure
        assert "trend_direction" in analysis
        assert "volatility" in analysis
        assert "mean_daily_change" in analysis
        assert "day_of_week_analysis" in analysis
        
        # Check day of week analysis
        day_analysis = analysis["day_of_week_analysis"]
        assert "average_volumes" in day_analysis
        assert "highest_volume_day" in day_analysis
        assert "lowest_volume_day" in day_analysis
    
    def test_analyze_volume_trends_insufficient_data(self):
        """Test analysis with insufficient data"""
        # Create data with only a few points
        data = {
            "volume_data": [[1000000000, 5000], [1000086400, 6000]]  # Only two points
        }
        
        # Call function
        analysis = analyze_volume_trends(data)
        
        # Verify error is returned
        assert "error" in analysis
        assert "Insufficient data" in analysis["error"]
    
    @patch('app.exchange_volume.api')
    def test_exchange_volume_cli_command_simulation(self, mock_api, mock_exchange_info_response, mock_volume_chart_data, capture_stdout):
        """Simulate the CLI command execution flow"""
        from app.exchange_volume import (
            get_exchange_volume_history, 
            save_exchange_volume_data,
            convert_date_to_timestamp,
            analyze_volume_trends
        )
        
        # Setup mocks for what would happen in the CLI command
        with patch('app.exchange_volume.get_exchange_info') as mock_get_info:
            mock_get_info.return_value = mock_exchange_info_response
            mock_api.get_exchange_volume_chart.return_value = mock_volume_chart_data
            
            # Simulate CLI command with date strings
            from_date = "2023-01-01"
            to_date = "2023-01-31"
            
            # Convert dates to timestamps
            from_timestamp = convert_date_to_timestamp(from_date)
            to_timestamp = convert_date_to_timestamp(to_date)
            
            # Get volume data
            volume_data = get_exchange_volume_history(
                exchange_id="binance",
                from_timestamp=from_timestamp,
                to_timestamp=to_timestamp,
                display=True
            )
            
            # Perform analysis
            if volume_data and volume_data.get("success", False):
                analysis = analyze_volume_trends(volume_data)
                
                # Check if analysis was performed
                assert "trend_direction" in analysis
                assert "volatility" in analysis
                assert "day_of_week_analysis" in analysis
            
            # Check output contains expected elements
            output = capture_stdout.getvalue()
            assert "Binance" in output
            assert "Volume Statistics" in output
            assert "Total Volume" in output
            
            # Verify the correct API calls were made
            mock_get_info.assert_called_with("binance")
            mock_api.get_exchange_volume_chart.assert_called_once()


@pytest.mark.parametrize("days,expected_call", [
    (7, 7),
    (30, 30),
    (90, 90),
    (365, 365)
])
def test_days_parameter_handling(days, expected_call):
    """Test that days parameter is properly handled"""
    with patch('app.exchange_volume.api') as mock_api:
        with patch('app.exchange_volume.get_exchange_info') as mock_get_info:
            # Setup mocks
            mock_get_info.return_value = {"id": "binance", "name": "Binance"}
            mock_api.get_exchange_volume_chart.return_value = []
            
            # Get timestamps that represent the days parameter
            now = int(time.time())
            from_timestamp = now - (days * 86400)
            
            # Call function
            get_exchange_volume_history(
                exchange_id="binance",
                from_timestamp=from_timestamp,
                to_timestamp=now,
                display=False
            )
            
            # The days_range parameter should match our expected call value
            call_args = mock_api.get_exchange_volume_chart.call_args[1]
            assert call_args.get("days_range") == expected_call
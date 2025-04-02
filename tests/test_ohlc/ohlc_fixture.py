from datetime import datetime
import pytest


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
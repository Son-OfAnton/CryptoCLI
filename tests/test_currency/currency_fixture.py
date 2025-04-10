"""
Mock fixtures for currency tests.
"""

# Add this to conftest.py as a fixture:

import pytest


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
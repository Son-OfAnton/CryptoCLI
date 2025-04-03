"""
Functionality for retrieving and displaying supported fiat currencies.
"""
from .api import api
from .utils.formatting import console, print_error
from rich.table import Table
from rich.text import Text
import json
import os

def get_supported_currencies(display=True, save=False, output=None):
    """
    Get and optionally display a list of supported vs currencies.
    
    Args:
        display (bool): Whether to display the currencies in the console
        save (bool): Whether to save the currencies to a file
        output (str, optional): Filename to save data to (if save is True)
        
    Returns:
        list: List of supported currency codes
    """
    try:
        # Get supported currencies from API
        currencies = api.get_supported_vs_currencies()
        
        if not currencies:
            print_error("No supported currencies found.")
            return None
            
        # Display currencies if requested
        if display:
            display_supported_currencies(currencies)
            
        # Save to file if requested
        if save:
            save_currencies_data(currencies, output)
            
        return currencies
        
    except Exception as e:
        print_error(f"Failed to retrieve supported currencies: {str(e)}")
        return None

def display_supported_currencies(currencies):
    """
    Display supported currencies in an organized table.
    
    Args:
        currencies (list): List of supported currency codes
    """
    # Create a table for displaying currencies
    table = Table(title="Supported Fiat Currencies for Price Conversion")
    
    # Define columns
    table.add_column("Code", style="cyan bold")
    table.add_column("Category", style="green")
    
    # Dictionary for categorizing currencies
    categories = {
        "fiat": ["usd", "eur", "jpy", "gbp", "aud", "cad", "chf", "cny", "hkd", "nzd", "sek", "krw", "sgd", "nok", "mxn", "inr", "rub", "zar", "try", "brl", "twd", "dkk", "pln", "thb", "idr", "huf", "czk", "ils", "clp", "php", "myr", "bgn", "ngn", "hrk", "rsd", "mad", "ars", "pkr", "sar", "aed", "bob", "cop", "pen", "uah", "vnd"],
        "commodity": ["xag", "xau"],
        "crypto": ["btc", "eth", "ltc", "bch", "bnb", "eos", "xrp", "xlm", "dot", "yfi", "aave", "link", "sats"]
    }
    
    # Group currencies by category
    sorted_currencies = sorted(currencies)
    for currency in sorted_currencies:
        currency_code = currency.lower()
        category = "Other"
        
        # Find category
        for cat, codes in categories.items():
            if currency_code in codes:
                category = cat.capitalize()
                break
                
        # Add row to table
        table.add_row(currency.upper(), category)
    
    # Display the table
    console.print(table)
    console.print(f"\nTotal supported currencies: {len(currencies)}")

def save_currencies_data(currencies, filename=None):
    """
    Save currencies data to a JSON file.
    
    Args:
        currencies (list): List of supported currency codes
        filename (str, optional): Filename to save data to
    """
    if filename is None:
        filename = "supported_currencies.json"
        
    try:
        # Prepare data for saving
        data = {
            "supported_currencies": currencies,
            "count": len(currencies)
        }
        
        # Write to file
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
            
        console.print(f"[green]Currency data saved to[/green] {filename}")
        
    except Exception as e:
        print_error(f"Failed to save currency data: {str(e)}")
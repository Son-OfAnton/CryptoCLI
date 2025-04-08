"""
Module for tracking and displaying CoinGecko API usage information.
"""
from typing import Dict, Any, Optional
import json
import os
from datetime import datetime
from rich.table import Table
from rich.panel import Panel
from rich.console import Console
from rich.layout import Layout
from rich.progress import Progress, BarColumn, TextColumn
from rich.text import Text

from app.api import api
from app.utils.formatting import (
    console,
    print_error,
    print_warning,
    print_success,
    format_large_number
)

def get_api_usage(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Get current CoinGecko API usage statistics.
    
    Args:
        force_refresh: If True, make a lightweight API call to refresh usage stats
        
    Returns:
        Dictionary containing usage statistics
    """
    # If force_refresh is True, make a lightweight API call to get fresh rate limit headers
    if force_refresh:
        try:
            # Make a lightweight API call that won't use many credits
            api.get_supported_vs_currencies()
        except Exception as e:
            print_warning(f"Failed to refresh API usage data: {str(e)}")
    
    # Return the current usage data
    return api.get_usage_stats()

def format_date(date_str: Optional[str]) -> str:
    """Format date string for display."""
    if not date_str:
        return "Never"
    
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%b %d, %Y")
    except ValueError:
        return date_str

def display_usage_stats(usage_data: Dict[str, Any]):
    """
    Display CoinGecko API usage statistics in a formatted view.
    
    Args:
        usage_data: Dictionary containing usage statistics
    """
    console.print("\n[bold blue]CoinGecko API Usage Statistics[/bold blue]\n")
    
    # Get rate limit information
    rate_limit_info = usage_data.get("rate_limit_info", {})
    
    # Create basic usage panel
    basic_usage_text = Text()
    basic_usage_text.append("API Key: ")
    if rate_limit_info.get("api_key"):
        basic_usage_text.append(f"[green]{rate_limit_info.get('api_key', 'Unknown')}[/green]\n")
    else:
        basic_usage_text.append("[yellow]Unknown[/yellow]\n")
    
    basic_usage_text.append(f"Total calls: {format_large_number(usage_data.get('total_calls', 0))}\n")
    basic_usage_text.append(f"Calls today: {format_large_number(usage_data.get('calls_today', 0))}\n")
    basic_usage_text.append(f"First API call: {format_date(usage_data.get('first_call_date'))}\n")
    basic_usage_text.append(f"Last API call: {format_date(usage_data.get('last_call_date'))}\n")
    
    basic_usage_panel = Panel(
        basic_usage_text,
        title="Basic Usage Information",
        border_style="blue"
    )
    
    console.print(basic_usage_panel)
    
    # Create rate limits panel
    if rate_limit_info:
        rate_limit_text = Text()
        
        # Add monthly credit information
        monthly_limit = rate_limit_info.get("credits_monthly_limit")
        if monthly_limit:
            used = rate_limit_info.get("credits_used_month", 0)
            remaining = rate_limit_info.get("credits_remaining_month", monthly_limit - used)
            
            rate_limit_text.append("Monthly credit limit: ")
            rate_limit_text.append(f"{format_large_number(monthly_limit)}\n")
            
            rate_limit_text.append("Credits used this month: ")
            rate_limit_text.append(f"{format_large_number(used)}\n")
            
            rate_limit_text.append("Credits remaining this month: ")
            if remaining > 0.2 * monthly_limit:
                rate_limit_text.append(f"[green]{format_large_number(remaining)}[/green]\n")
            elif remaining > 0.05 * monthly_limit:
                rate_limit_text.append(f"[yellow]{format_large_number(remaining)}[/yellow]\n")
            else:
                rate_limit_text.append(f"[red]{format_large_number(remaining)}[/red]\n")
                
            # Add monthly usage progress bar
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console
            ) as progress:
                task = progress.add_task("[cyan]Usage", total=monthly_limit)
                progress.update(task, completed=used)
        
        # Add second-based rate limit information
        if "credits_remaining_second" in rate_limit_info:
            rate_limit_text.append("\nCredits remaining per second: ")
            rate_limit_text.append(f"{rate_limit_info['credits_remaining_second']}\n")
        
        # Add minute-based rate limit information
        if "credits_remaining_minute" in rate_limit_info:
            rate_limit_text.append("Credits remaining per minute: ")
            rate_limit_text.append(f"{rate_limit_info['credits_remaining_minute']}\n")
        
        # Add standard rate limit information
        if "limit" in rate_limit_info and "remaining" in rate_limit_info:
            rate_limit_text.append("\nOverall rate limit: ")
            rate_limit_text.append(f"{rate_limit_info['limit']}\n")
            
            rate_limit_text.append("Remaining requests: ")
            remaining_requests = rate_limit_info['remaining']
            if remaining_requests > 0.5 * rate_limit_info['limit']:
                rate_limit_text.append(f"[green]{remaining_requests}[/green]\n")
            elif remaining_requests > 0.2 * rate_limit_info['limit']:
                rate_limit_text.append(f"[yellow]{remaining_requests}[/yellow]\n")
            else:
                rate_limit_text.append(f"[red]{remaining_requests}[/red]\n")
            
            # Add when the rate limit will reset
            if "reset" in rate_limit_info:
                reset_time = datetime.fromtimestamp(rate_limit_info['reset'])
                rate_limit_text.append("Rate limit resets at: ")
                rate_limit_text.append(f"{reset_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        rate_limit_panel = Panel(
            rate_limit_text,
            title="Rate Limit Information",
            border_style="green"
        )
        
        console.print(rate_limit_panel)
    
    # Display monthly usage table if available
    monthly_usage = usage_data.get("monthly_usage", {})
    if monthly_usage:
        console.print("\n[bold]Monthly Usage:[/bold]")
        
        table = Table(title="API Calls by Month")
        table.add_column("Month", style="cyan")
        table.add_column("Calls", style="magenta", justify="right")
        
        # Sort months in reverse chronological order
        sorted_months = sorted(monthly_usage.keys(), reverse=True)
        
        for month in sorted_months[:12]:  # Show last 12 months
            try:
                date_obj = datetime.strptime(month, "%Y-%m")
                month_formatted = date_obj.strftime("%b %Y")
            except ValueError:
                month_formatted = month
                
            table.add_row(month_formatted, format_large_number(monthly_usage[month]))
        
        console.print(table)
    
    # Display endpoints usage
    endpoints = usage_data.get("endpoints_called", {})
    if endpoints:
        console.print("\n[bold]Endpoint Usage:[/bold]")
        
        table = Table(title="API Calls by Endpoint")
        table.add_column("Endpoint", style="cyan")
        table.add_column("Calls", style="magenta", justify="right")
        
        # Sort endpoints by call count, descending
        sorted_endpoints = sorted(endpoints.items(), key=lambda item: item[1], reverse=True)
        
        for endpoint, count in sorted_endpoints[:15]:  # Show top 15 endpoints
            table.add_row(endpoint, format_large_number(count))
        
        console.print(table)
    
    # Provide some recommendations based on usage
    if rate_limit_info:
        console.print("\n[bold]Recommendations:[/bold]")
        
        monthly_limit = rate_limit_info.get("credits_monthly_limit", 0)
        remaining = rate_limit_info.get("credits_remaining_month", 0)
        
        if monthly_limit and remaining < 0.1 * monthly_limit:
            print_warning("Monthly credits are running low. Consider upgrading your plan or reducing API usage.")
        
        if usage_data.get("calls_today", 0) > 1000:
            print_warning("High volume of API calls today. Check if there are inefficient or redundant API requests.")
        
        # Calculate average daily usage this month
        current_month = datetime.now().strftime("%Y-%m")
        month_usage = monthly_usage.get(current_month, 0)
        day_of_month = datetime.now().day
        
        if day_of_month > 0 and month_usage > 0:
            avg_daily = month_usage / day_of_month
            expected_monthly = avg_daily * 30  # Approximate month length
            
            if monthly_limit and expected_monthly > monthly_limit:
                print_warning(f"At current usage rate ({int(avg_daily)} calls/day), you will likely exceed your monthly limit.")
            else:
                print_success(f"Current usage rate ({int(avg_daily)} calls/day) is within your monthly limit.")

def save_api_usage_export(usage_data: Dict[str, Any], filename: Optional[str] = None) -> str:
    """
    Save API usage statistics to a JSON file.
    
    Args:
        usage_data: Dictionary containing usage statistics
        filename: Optional custom filename to save data to
        
    Returns:
        Path to the saved file
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"coingecko_api_usage_{timestamp}.json"
    
    # Ensure the filename has a .json extension
    if not filename.endswith('.json'):
        filename += '.json'
    
    # Write data to file
    with open(filename, 'w') as f:
        json.dump(usage_data, f, indent=4)
    
    return os.path.abspath(filename)
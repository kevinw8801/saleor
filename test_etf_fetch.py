#!/usr/bin/env python3
"""
Test script to verify ETF fetching functionality
"""
import os
import sys
import django

# Add the project to Python path
sys.path.insert(0, '/home/appserv/projects/walsai/tradinglab/saleor/saleor')

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saleor.settings')
django.setup()

from saleor.plugins.securities.models import Tickers
from saleor.plugins.securities.startup import initialize_tickers_data

def test_current_tickers():
    """Test current ticker counts"""
    print("=== Current Ticker Status ===")
    total_count = Tickers.objects.count()
    stocks_count = Tickers.objects.filter(type='cs').count()
    etfs_count = Tickers.objects.filter(type='etp').count()
    
    print(f"Total tickers: {total_count}")
    print(f"Stocks (cs): {stocks_count}")
    print(f"ETFs (etp): {etfs_count}")
    
    # Show sample ETF records if any exist
    etf_samples = Tickers.objects.filter(type='etp')[:5]
    print(f"\nSample ETF records ({len(etf_samples)}):")
    for etf in etf_samples:
        print(f"  {etf.ticker} - {etf.name} ({etf.type})")
    
    return total_count, stocks_count, etfs_count

def test_reinitialize():
    """Test reinitializing tickers"""
    print("\n=== Testing Reinitialization ===")
    
    # Clear existing data to test fresh initialization
    Tickers.objects.all().delete()
    print("Cleared existing ticker data")
    
    # Run initialization
    initialize_tickers_data()
    
    # Check results
    test_current_tickers()

if __name__ == "__main__":
    print("Testing ETF fetching functionality...")
    
    # Test current state
    total, stocks, etfs = test_current_tickers()
    
    if etfs == 0:
        print(f"\n⚠️  No ETFs found in database. Testing reinitialization...")
        test_reinitialize()
    else:
        print(f"\n✅ ETFs found: {etfs}")
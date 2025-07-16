from django.core.management.base import BaseCommand
from saleor.plugins.securities.models import Tickers
from saleor.plugins.securities.startup import (
    fetch_us_stocks_and_etfs,
    fetch_us_etfs_specifically,
    combine_and_deduplicate_tickers,
    bulk_insert_tickers
)
from saleor.polygon.clients import PolygonIOClient
import logging

# Set up logging to see debug messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Debug ETF fetching issue step by step'

    def handle(self, *args, **options):
        self.stdout.write("=== Debugging ETF Issue ===\n")
        
        # Step 1: Check current database state
        self.stdout.write("Step 1: Current database state")
        self.check_database_state()
        
        # Step 2: Test Polygon.io client
        self.stdout.write("\nStep 2: Testing Polygon.io client")
        try:
            polygon_client = PolygonIOClient()
            self.stdout.write(self.style.SUCCESS("✅ Polygon.io client initialized successfully"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to initialize Polygon.io client: {e}"))
            return
        
        # Step 3: Test general stocks/ETFs fetch
        self.stdout.write("\nStep 3: Testing general stocks/ETFs fetch")
        try:
            stocks_and_etfs = fetch_us_stocks_and_etfs(polygon_client)
            total_general = len(stocks_and_etfs)
            cs_count = len([t for t in stocks_and_etfs if t.get('type') == 'cs'])
            etp_count = len([t for t in stocks_and_etfs if t.get('type') == 'etp'])
            
            self.stdout.write(f"  Total from general fetch: {total_general}")
            self.stdout.write(f"  Stocks (cs): {cs_count}")
            self.stdout.write(f"  ETFs (etp): {etp_count}")
            
            # Show sample ETFs from general fetch
            etf_samples = [t for t in stocks_and_etfs if t.get('type') == 'etp'][:5]
            if etf_samples:
                self.stdout.write("  Sample ETFs from general fetch:")
                for etf in etf_samples:
                    self.stdout.write(f"    {etf.get('ticker')} - {etf.get('name')}")
            else:
                self.stdout.write(self.style.WARNING("  ⚠️  No ETFs found in general fetch"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ General fetch failed: {e}"))
            stocks_and_etfs = []
        
        # Step 4: Test ETF-specific fetch
        self.stdout.write("\nStep 4: Testing ETF-specific fetch")
        try:
            etfs_specific = fetch_us_etfs_specifically(polygon_client)
            self.stdout.write(f"  ETFs from specific fetch: {len(etfs_specific)}")
            
            # Show sample ETFs from specific fetch
            if etfs_specific:
                self.stdout.write("  Sample ETFs from specific fetch:")
                for etf in etfs_specific[:5]:
                    self.stdout.write(f"    {etf.get('ticker')} - {etf.get('name')}")
            else:
                self.stdout.write(self.style.WARNING("  ⚠️  No ETFs found in specific fetch"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ ETF-specific fetch failed: {e}"))
            etfs_specific = []
        
        # Step 5: Test combination and deduplication
        self.stdout.write("\nStep 5: Testing combination and deduplication")
        try:
            combined_data = combine_and_deduplicate_tickers(stocks_and_etfs, etfs_specific)
            total_combined = len(combined_data)
            cs_combined = len([t for t in combined_data if t.get('type') == 'cs'])
            etp_combined = len([t for t in combined_data if t.get('type') == 'etp'])
            
            self.stdout.write(f"  Total combined: {total_combined}")
            self.stdout.write(f"  Stocks (cs): {cs_combined}")
            self.stdout.write(f"  ETFs (etp): {etp_combined}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Combination failed: {e}"))
            combined_data = []
        
        # Step 6: Test bulk insert (if we have data)
        if combined_data:
            self.stdout.write("\nStep 6: Testing bulk insert")
            try:
                # Clear existing data first
                Tickers.objects.all().delete()
                
                inserted_count = bulk_insert_tickers(combined_data)
                self.stdout.write(f"  Inserted: {inserted_count} tickers")
                
                # Check final database state
                self.stdout.write("\nFinal database state:")
                self.check_database_state()
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Bulk insert failed: {e}"))
        else:
            self.stdout.write(self.style.WARNING("\nSkipping bulk insert - no data to insert"))

    def check_database_state(self):
        """Check and display current database state"""
        try:
            total_count = Tickers.objects.count()
            stocks_count = Tickers.objects.filter(type='cs').count()
            etfs_count = Tickers.objects.filter(type='etp').count()
            
            self.stdout.write(f"  Total tickers: {total_count}")
            self.stdout.write(f"  Stocks (cs): {stocks_count}")
            self.stdout.write(f"  ETFs (etp): {etfs_count}")
            
            # Show sample ETFs if any
            if etfs_count > 0:
                self.stdout.write("  Sample ETFs in database:")
                etf_samples = Tickers.objects.filter(type='etp')[:5]
                for etf in etf_samples:
                    self.stdout.write(f"    {etf.ticker} - {etf.name}")
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Database check failed: {e}"))
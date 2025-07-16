from django.core.management.base import BaseCommand
from saleor.plugins.securities.models import Tickers
from saleor.plugins.securities.startup import initialize_tickers_data


class Command(BaseCommand):
    help = 'Test ETF fetching functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reinitialize',
            action='store_true',
            help='Clear existing data and reinitialize'
        )

    def handle(self, *args, **options):
        self.stdout.write("=== Testing ETF Fetching Functionality ===\n")
        
        # Check current state
        self.check_current_state()
        
        if options['reinitialize']:
            self.reinitialize_data()
            self.check_current_state()
        
        # Check for ETFs
        etfs_count = Tickers.objects.filter(type='etp').count()
        
        if etfs_count == 0:
            self.stdout.write(self.style.WARNING("⚠️  No ETFs found in database"))
            self.stdout.write("Consider running with --reinitialize to fetch fresh data")
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ Found {etfs_count} ETFs"))
            
            # Show sample ETFs
            self.stdout.write("\nSample ETF records:")
            etf_samples = Tickers.objects.filter(type='etp')[:10]
            for etf in etf_samples:
                self.stdout.write(f"  {etf.ticker} - {etf.name}")

    def check_current_state(self):
        """Check and display current ticker counts"""
        total_count = Tickers.objects.count()
        stocks_count = Tickers.objects.filter(type='cs').count()
        etfs_count = Tickers.objects.filter(type='etp').count()
        
        self.stdout.write(f"Current ticker counts:")
        self.stdout.write(f"  Total: {total_count}")
        self.stdout.write(f"  Stocks (cs): {stocks_count}")
        self.stdout.write(f"  ETFs (etp): {etfs_count}")
        self.stdout.write("")

    def reinitialize_data(self):
        """Clear and reinitialize ticker data"""
        self.stdout.write("Clearing existing ticker data...")
        Tickers.objects.all().delete()
        
        self.stdout.write("Reinitializing ticker data...")
        initialize_tickers_data()
        self.stdout.write("")
from django.core.management.base import BaseCommand
from saleor.plugins.securities.models import Tickers
from saleor.plugins.securities.startup import initialize_tickers_data
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test the updated exchange fetching logic for stocks and ETFs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-first',
            action='store_true',
            help='Clear existing tickers before fetching new ones',
        )

    def handle(self, *args, **options):
        self.stdout.write("=== Testing Updated Exchange Fetching Logic ===\n")
        
        # Check current state
        self.stdout.write("Current database state:")
        self.check_database_state()
        
        # Clear if requested
        if options['clear_first']:
            self.stdout.write("\nClearing existing tickers...")
            Tickers.objects.all().delete()
            self.stdout.write("Tickers cleared.")
        
        # Run the updated fetching logic
        self.stdout.write("\nRunning updated fetching logic...")
        try:
            initialize_tickers_data()
            self.stdout.write(self.style.SUCCESS("✅ Fetching completed successfully"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Fetching failed: {e}"))
            return
        
        # Check final state
        self.stdout.write("\nFinal database state:")
        self.check_database_state()
        
        # Show exchange breakdown
        self.show_exchange_breakdown()

    def check_database_state(self):
        """Check and display current database state"""
        try:
            total_count = Tickers.objects.count()
            stocks_count = Tickers.objects.filter(type='cs').count()
            etfs_count = Tickers.objects.filter(type='etp').count()
            
            self.stdout.write(f"  Total tickers: {total_count}")
            self.stdout.write(f"  Stocks (cs): {stocks_count}")
            self.stdout.write(f"  ETFs (etp): {etfs_count}")
            
            if etfs_count > 0:
                self.stdout.write("  Sample ETFs:")
                etf_samples = Tickers.objects.filter(type='etp')[:5]
                for etf in etf_samples:
                    self.stdout.write(f"    {etf.ticker} ({etf.exchange}) - {etf.name}")
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Database check failed: {e}"))

    def show_exchange_breakdown(self):
        """Show breakdown by exchange"""
        self.stdout.write("\nExchange breakdown:")
        try:
            # Get unique exchanges
            exchanges = Tickers.objects.values_list('exchange', flat=True).distinct()
            
            for exchange in sorted(exchanges):
                if exchange:  # Skip empty exchanges
                    total = Tickers.objects.filter(exchange=exchange).count()
                    stocks = Tickers.objects.filter(exchange=exchange, type='cs').count()
                    etfs = Tickers.objects.filter(exchange=exchange, type='etp').count()
                    self.stdout.write(f"  {exchange}: {total} total (Stocks: {stocks}, ETFs: {etfs})")
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Exchange breakdown failed: {e}"))
from django.core.management.base import BaseCommand
from ...models import Tickers
from ....plugins.securities.startup import initialize_tickers_data


class Command(BaseCommand):
    help = 'Initialize ticker data from Polygon.io API'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force initialization even if tickers already exist',
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Starting comprehensive ticker initialization (US stocks and ETFs)...')
        
        if options['force']:
            self.stdout.write('Force mode enabled - will initialize regardless of current count')
            # Temporarily override the count check
            original_count = Tickers.objects.count()
            stocks_count = Tickers.objects.filter(type='cs').count()
            etfs_count = Tickers.objects.filter(type='etp').count()
            self.stdout.write(f'Current ticker count: {original_count} ({stocks_count} stocks, {etfs_count} ETFs)')
            initialize_tickers_data()
        else:
            initialize_tickers_data()
        
        final_count = Tickers.objects.count()
        final_stocks = Tickers.objects.filter(type='cs').count()
        final_etfs = Tickers.objects.filter(type='etp').count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Ticker initialization complete. Final count: {final_count} '
                f'({final_stocks} stocks, {final_etfs} ETFs)'
            )
        )
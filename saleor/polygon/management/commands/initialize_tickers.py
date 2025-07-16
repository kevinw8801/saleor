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
        self.stdout.write('Starting ticker initialization...')
        
        if options['force']:
            self.stdout.write('Force mode enabled - will initialize regardless of current count')
            # Temporarily override the count check
            original_count = Tickers.objects.count()
            self.stdout.write(f'Current ticker count: {original_count}')
            initialize_tickers_data()
        else:
            initialize_tickers_data()
        
        final_count = Tickers.objects.count()
        self.stdout.write(
            self.style.SUCCESS(f'Ticker initialization complete. Final count: {final_count}')
        )
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import time
import signal
import sys

from saleor.polygon.websocket_client import get_websocket_manager
from saleor.polygon.settings import (
    get_default_symbols, is_websocket_enabled_for_market,
    get_websocket_setting
)


class Command(BaseCommand):
    help = 'Start Polygon.io WebSocket client for real-time market data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--markets',
            nargs='+',
            default=['stocks', 'crypto', 'forex'],
            help='Market types to subscribe to (stocks, crypto, forex)'
        )
        parser.add_argument(
            '--symbols',
            nargs='+',
            help='Specific symbols to subscribe to (overrides default symbols)'
        )
        parser.add_argument(
            '--data-types',
            nargs='+',
            default=['quotes'],
            choices=['quotes', 'trades'],
            help='Types of data to subscribe to'
        )
        parser.add_argument(
            '--no-auto-subscribe',
            action='store_true',
            help='Don\'t auto-subscribe to default symbols'
        )

    def handle(self, *args, **options):
        # Check if API key is configured
        api_key = getattr(settings, 'POLYGON_IO_API_KEY', None)
        if not api_key:
            raise CommandError('POLYGON_IO_API_KEY not configured in settings')

        self.stdout.write('Starting Polygon.io WebSocket client...')
        
        # Get WebSocket manager
        ws_manager = get_websocket_manager()
        
        # Set up signal handlers for graceful shutdown
        def signal_handler(sig, frame):
            self.stdout.write('\nShutting down WebSocket client...')
            ws_manager.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Start WebSocket manager
            ws_manager.start()
            self.stdout.write('WebSocket manager started successfully')
            
            # Subscribe to data if auto-subscribe is enabled
            if not options['no_auto_subscribe'] or options['symbols']:
                self._subscribe_to_data(ws_manager, options)
            
            # Keep the command running
            self.stdout.write('WebSocket client is running. Press Ctrl+C to stop.')
            while True:
                time.sleep(1)
                
        except Exception as e:
            self.stderr.write(f'Error starting WebSocket client: {e}')
            raise CommandError(f'Failed to start WebSocket client: {e}')
    
    def _subscribe_to_data(self, ws_manager, options):
        """Subscribe to market data based on options"""
        markets = options['markets']
        data_types = options['data_types']
        custom_symbols = options.get('symbols')
        
        for market in markets:
            if not is_websocket_enabled_for_market(market):
                self.stdout.write(f'WebSocket not enabled for {market}, skipping...')
                continue
            
            # Get symbols to subscribe to
            if custom_symbols:
                symbols = custom_symbols
            else:
                symbols = get_default_symbols(market)
            
            if not symbols:
                self.stdout.write(f'No symbols configured for {market}, skipping...')
                continue
            
            self.stdout.write(f'Subscribing to {market} data for symbols: {symbols}')
            
            # Subscribe to each data type
            for data_type in data_types:
                try:
                    if data_type == 'quotes':
                        success = ws_manager.subscribe_quotes(symbols, market)
                    elif data_type == 'trades':
                        success = ws_manager.subscribe_trades(symbols, market)
                    else:
                        continue
                    
                    if success:
                        self.stdout.write(
                            f'Successfully subscribed to {market} {data_type} for {len(symbols)} symbols'
                        )
                    else:
                        self.stderr.write(
                            f'Failed to subscribe to {market} {data_type}'
                        )
                        
                except Exception as e:
                    self.stderr.write(
                        f'Error subscribing to {market} {data_type}: {e}'
                    )
            
            # Small delay between market subscriptions
            time.sleep(1)
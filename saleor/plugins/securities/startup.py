import logging
from typing import Dict, List, Any
from django.db import transaction
from django.conf import settings

logger = logging.getLogger(__name__)


def initialize_tickers_data():
    """
    Initialize tickers data from Polygon.io API on startup.
    
    This function:
    1. Checks the number of records in the tickers table
    2. If count > 5000, does nothing
    3. Otherwise, fetches US stocks and ETFs from Polygon.io and populates the table
    """
    try:
        # Import here to avoid circular imports
        from ...polygon.clients import PolygonIOClient
        from ...polygon.models import Tickers
        
        # Check current ticker count
        ticker_count = Tickers.objects.count()
        logger.info(f"Current ticker count: {ticker_count}")
        
        if ticker_count > 5000:
            logger.info("Ticker count > 5000, skipping initialization")
            return
        
        logger.info("Initializing tickers data from Polygon.io...")
        
        # Initialize Polygon.io client
        try:
            polygon_client = PolygonIOClient()
        except ValueError as e:
            logger.error(f"Failed to initialize Polygon.io client: {e}")
            return
        
        # Fetch US stocks and ETFs
        tickers_data = fetch_us_stocks_and_etfs(polygon_client)
        
        if not tickers_data:
            logger.warning("No ticker data retrieved from Polygon.io")
            return
        
        # Bulk insert tickers
        inserted_count = bulk_insert_tickers(tickers_data)
        logger.info(f"Successfully inserted {inserted_count} tickers")
        
    except Exception as e:
        logger.error(f"Error initializing tickers data: {e}")


def fetch_us_stocks_and_etfs(polygon_client) -> List[Dict[str, Any]]:
    """
    Fetch US stocks and ETFs from Polygon.io v3/reference/tickers endpoint.
    
    Returns:
        List of ticker dictionaries with required fields
    """
    tickers_data = []
    next_url = None
    
    try:
        while True:
            # Prepare request parameters
            params = {
                'market': 'stocks',  # US stocks market
                'active': 'true',
                'limit': 1000  # Maximum allowed per request
            }
            
            # Make API request
            if next_url:
                # Use cursor-based pagination
                response = polygon_client._make_request(next_url.replace(polygon_client.BASE_URL, ''))
            else:
                response = polygon_client._make_request('/v3/reference/tickers', params)
            
            # Process response
            if response.get('status') == 'OK' and 'results' in response:
                results = response['results']
                
                for ticker_data in results:
                    # Filter for US stocks and ETFs only
                    ticker_type = ticker_data.get('type')
                    market = ticker_data.get('market', '').lower()
                    
                    # Only include Common Stock (CS) and Exchange Traded Products (ETP)
                    if ticker_type in ['CS', 'ETP'] and market == 'stocks':
                        processed_ticker = {
                            'ticker': ticker_data.get('ticker', '').upper(),
                            'name': ticker_data.get('name', '')[:255],  # Limit to 255 chars
                            'type': 'cs' if ticker_type == 'CS' else 'etp',
                            'exchange': ticker_data.get('primary_exchange', '')[:10],  # Limit to 10 chars
                            'active': ticker_data.get('active', True)
                        }
                        
                        # Only add if ticker symbol is valid
                        if processed_ticker['ticker'] and len(processed_ticker['ticker']) <= 10:
                            tickers_data.append(processed_ticker)
                
                # Check for pagination
                next_url = response.get('next_url')
                if not next_url:
                    break
                    
                # Add small delay to respect rate limits
                import time
                time.sleep(0.1)
                
            else:
                logger.error(f"Invalid response from Polygon.io: {response}")
                break
                
    except Exception as e:
        logger.error(f"Error fetching tickers from Polygon.io: {e}")
    
    logger.info(f"Fetched {len(tickers_data)} tickers from Polygon.io")
    return tickers_data


def bulk_insert_tickers(tickers_data: List[Dict[str, Any]]) -> int:
    """
    Bulk insert ticker data into the tickers table.
    
    Args:
        tickers_data: List of ticker dictionaries
        
    Returns:
        Number of tickers inserted
    """
    if not tickers_data:
        return 0
    
    try:
        # Import here to avoid circular imports
        from ...polygon.models import Tickers
        
        with transaction.atomic():
            # Create ticker objects
            ticker_objects = []
            for ticker_data in tickers_data:
                ticker_obj = Tickers(
                    ticker=ticker_data['ticker'],
                    name=ticker_data['name'],
                    type=ticker_data['type'],
                    exchange=ticker_data['exchange'],
                    active=ticker_data['active']
                )
                ticker_objects.append(ticker_obj)
            
            # Get count before bulk create
            count_before = Tickers.objects.count()
            
            # Bulk create with ignore_conflicts to handle duplicates
            Tickers.objects.bulk_create(
                ticker_objects,
                ignore_conflicts=True,
                batch_size=1000
            )
            
            # Get count after to determine how many were actually inserted
            count_after = Tickers.objects.count()
            
            return count_after - count_before
            
    except Exception as e:
        logger.error(f"Error bulk inserting tickers: {e}")
        return 0
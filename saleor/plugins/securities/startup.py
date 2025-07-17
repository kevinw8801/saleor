import logging
from typing import Dict, List, Any
from django.db import transaction
from django.conf import settings

logger = logging.getLogger(__name__)


def initialize_tickers_data():
    """
    Initialize tickers data from Polygon.io API on startup.
    
    This function:
    1. Checks if the tickers table exists
    2. Checks the number of records in the tickers table
    3. If count > 5000, does nothing
    4. Otherwise, fetches US stocks and ETFs from Polygon.io and populates the table
    """
    try:
        # Import here to avoid circular imports
        from django.db import connection
        from ...polygon.clients import PolygonIOClient
        from .models import Tickers
        
        # Check if tickers table exists
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'tickers'
                );
            """)
            table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            logger.info("Tickers table does not exist yet, skipping initialization. Will retry on next startup.")
            return
        
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
            logger.info("To configure Polygon.io API key, set POLYGON_IO_API_KEY environment variable or update settings.py")
            logger.info("A default API key is configured but may have rate limits. For production, get your own key from https://polygon.io/")
            return
        
        # Fetch US stocks and ETFs
        logger.info("Fetching US stocks and ETFs from Polygon.io...")
        stocks_and_etfs_data = fetch_us_stocks_and_etfs(polygon_client)
        
        # Also fetch ETFs specifically to ensure comprehensive coverage
        logger.info("Fetching additional ETF data from Polygon.io...")
        etf_data = fetch_us_etfs_specifically(polygon_client)
        
        # Combine data and remove duplicates
        tickers_data = combine_and_deduplicate_tickers(stocks_and_etfs_data, etf_data)
        
        if not tickers_data:
            logger.warning("No ticker data retrieved from Polygon.io")
            logger.info("This may be due to rate limiting. Try again later or upgrade your Polygon.io plan.")
            return
        
        # Bulk insert tickers
        inserted_count = bulk_insert_tickers(tickers_data)
        final_count = inserted_count
        
        if inserted_count > 0:
            # Count final results by type
            total_tickers = Tickers.objects.count()
            stocks_count = Tickers.objects.filter(type='cs').count()
            etfs_count = Tickers.objects.filter(type='etp').count()
            
            logger.info(f"Successfully inserted {inserted_count} new tickers from Polygon.io")
            logger.info(f"Database now contains {total_tickers} total tickers: {stocks_count} stocks, {etfs_count} ETFs")
            logger.info("Ticker initialization completed with comprehensive US market coverage.")
            
            if inserted_count < 5000:
                logger.info("Note: Due to API rate limits, this may be a partial dataset.")
                logger.info("Run the initialization again later to fetch more tickers, or upgrade your Polygon.io plan.")
        else:
            logger.warning("No new tickers were inserted (may be duplicates or empty dataset)")
        
    except Exception as e:
        logger.error(f"Error initializing tickers data: {e}")


def fetch_us_stocks_and_etfs(polygon_client) -> List[Dict[str, Any]]:
    """
    Fetch US stocks and ETFs from Polygon.io from all major US exchanges.
    Includes NYSE, NASDAQ, NYSE American, Cboe BZX, IEX, OTC Markets, and other Cboe exchanges.
    Uses rate limiting and handles API errors gracefully.
    
    Returns:
        List of ticker dictionaries with required fields
    """
    tickers_data = []
    next_url = None
    request_count = 0
    max_requests = 8  # Increased to cover more exchanges
    
    # Major US exchanges to ensure comprehensive coverage
    target_exchanges = [
        'XNYS',   # NYSE
        'XNAS',   # NASDAQ
        'XASE',   # NYSE American
        'XBZX',   # Cboe BZX
        'IEXG',   # IEX
        'OTCQ',   # OTC Markets - OTCQX
        'OTCQB',  # OTC Markets - OTCQB
        'OTCPK'   # OTC Markets - Pink
    ]
    
    try:
        while True:
            # Rate limiting check
            if request_count >= max_requests:
                logger.warning(f"Reached rate limit of {max_requests} requests. Stopping ticker fetch to avoid 429 errors.")
                logger.info("For more data, consider upgrading Polygon.io plan or running this process during off-peak hours.")
                break
            
            # Prepare request parameters - Remove market restriction to get all securities
            params = {
                'active': 'true',
                'limit': 1000  # Maximum allowed per request
            }
            
            try:
                # Make API request with error handling
                if next_url:
                    # Use cursor-based pagination
                    response = polygon_client._make_request(next_url.replace(polygon_client.BASE_URL, ''))
                else:
                    response = polygon_client._make_request('/v3/reference/tickers', params)
                
                request_count += 1
                
            except Exception as api_error:
                if "429" in str(api_error) or "Too Many Requests" in str(api_error):
                    logger.warning("Hit rate limit (429). Stopping fetch to avoid further rate limiting.")
                    logger.info(f"Successfully fetched {len(tickers_data)} tickers before hitting rate limit.")
                    break
                else:
                    logger.error(f"API request failed: {api_error}")
                    break
            
            # Process response
            if response.get('status') == 'OK' and 'results' in response:
                results = response['results']
                
                for ticker_data in results:
                    # Filter for US stocks and ETFs from major exchanges
                    ticker_type = ticker_data.get('type')
                    primary_exchange = ticker_data.get('primary_exchange', '')
                    market = ticker_data.get('market', '').lower()
                    
                    # Include Common Stock (CS) and Exchange Traded Products (ETP/ETF)
                    # Accept from major US exchanges or general stock markets
                    valid_type = ticker_type in ['CS', 'ETP', 'ETF']
                    valid_exchange = primary_exchange in target_exchanges
                    valid_market = market in ['stocks', 'otc', 'fx']  # Expanded market types
                    
                    if valid_type and (valid_exchange or valid_market):
                        # Map different ETF types to 'etp'
                        mapped_type = 'cs' if ticker_type == 'CS' else 'etp'
                        
                        processed_ticker = {
                            'ticker': ticker_data.get('ticker', '').upper(),
                            'name': ticker_data.get('name', '')[:255],  # Limit to 255 chars
                            'type': mapped_type,
                            'exchange': primary_exchange[:10],  # Limit to 10 chars
                            'active': ticker_data.get('active', True)
                        }
                        
                        # Only add if ticker symbol is valid and from target exchanges
                        if (processed_ticker['ticker'] and 
                            len(processed_ticker['ticker']) <= 10 and
                            processed_ticker['exchange']):
                            tickers_data.append(processed_ticker)
                            
                            # Log ETF finds for debugging
                            if mapped_type == 'etp':
                                logger.debug(f"Found ETF: {processed_ticker['ticker']} from {primary_exchange}")
                
                # Count types for better debugging
                cs_count = len([t for t in tickers_data if t.get('type') == 'cs'])
                etp_count = len([t for t in tickers_data if t.get('type') == 'etp'])
                logger.info(f"Processed page {request_count}, got {len(results)} tickers. Total so far: {len(tickers_data)} (CS: {cs_count}, ETP: {etp_count})")
                
                # Check for pagination
                next_url = response.get('next_url')
                if not next_url:
                    logger.info("No more pages to fetch.")
                    break
                    
                # Add delay to respect rate limits (free tier: 5 requests per minute)
                import time
                time.sleep(12)  # 12 seconds between requests = 5 requests per minute
                
            else:
                logger.error(f"Invalid response from Polygon.io: {response}")
                break
                
    except Exception as e:
        logger.error(f"Error fetching tickers from Polygon.io: {e}")
    
    logger.info(f"Finished fetching. Total tickers collected: {len(tickers_data)}")
    # Final summary
    cs_count = len([t for t in tickers_data if t.get('type') == 'cs'])
    etp_count = len([t for t in tickers_data if t.get('type') == 'etp'])
    logger.info(f"General fetch completed: {len(tickers_data)} total tickers (CS: {cs_count}, ETP: {etp_count}) from {request_count} API requests")
    
    return tickers_data


def fetch_us_etfs_specifically(polygon_client) -> List[Dict[str, Any]]:
    """
    Fetch US ETFs specifically from Polygon.io v3/reference/tickers endpoint.
    This makes a targeted call for ETFs to ensure comprehensive coverage from all major exchanges.
    
    Returns:
        List of ETF ticker dictionaries
    """
    etf_data = []
    next_url = None
    request_count = 0
    max_requests = 5  # Increased for better ETF coverage
    
    # Major US exchanges for ETFs
    target_exchanges = [
        'XNYS',   # NYSE - many ETFs
        'XNAS',   # NASDAQ - ~4,351 ETFs
        'XASE',   # NYSE American - some ETFs
        'XBZX',   # Cboe BZX - ETFs and some stocks
        'IEXG',   # IEX - stocks and ETFs
        'XBYX',   # Other Cboe exchanges
        'XEDA',   # Other Cboe exchanges
        'XEDG'    # Other Cboe exchanges
    ]
    
    try:
        while True:
            # Rate limiting check
            if request_count >= max_requests:
                logger.info(f"Reached ETF request limit of {max_requests}. Collected {len(etf_data)} ETFs.")
                break
            
            # Prepare request parameters specifically for ETFs - Remove market restriction
            params = {
                'type': 'ETP',       # Exchange Traded Products (ETFs)
                'active': 'true',
                'limit': 1000
            }
            
            try:
                # Make API request
                if next_url:
                    response = polygon_client._make_request(next_url.replace(polygon_client.BASE_URL, ''))
                else:
                    response = polygon_client._make_request('/v3/reference/tickers', params)
                
                request_count += 1
                
            except Exception as api_error:
                if "429" in str(api_error) or "Too Many Requests" in str(api_error):
                    logger.warning("Hit rate limit during ETF fetch. Stopping ETF-specific fetch.")
                    break
                else:
                    logger.error(f"ETF API request failed: {api_error}")
                    break
            
            # Process response
            if response.get('status') == 'OK' and 'results' in response:
                results = response['results']
                
                for ticker_data in results:
                    # Filter for US ETFs from major exchanges
                    ticker_type = ticker_data.get('type')
                    primary_exchange = ticker_data.get('primary_exchange', '')
                    market = ticker_data.get('market', '').lower()
                    
                    # Include Exchange Traded Products (ETP/ETF) from major exchanges
                    valid_type = ticker_type in ['ETP', 'ETF']
                    valid_exchange = primary_exchange in target_exchanges
                    valid_market = market in ['stocks', 'otc', 'fx']  # Expanded market types
                    
                    if valid_type and (valid_exchange or valid_market):
                        processed_ticker = {
                            'ticker': ticker_data.get('ticker', '').upper(),
                            'name': ticker_data.get('name', '')[:255],
                            'type': 'etp',
                            'exchange': primary_exchange[:10],
                            'active': ticker_data.get('active', True)
                        }
                        
                        # Only add if ticker symbol is valid and from target exchanges
                        if (processed_ticker['ticker'] and 
                            len(processed_ticker['ticker']) <= 10 and
                            processed_ticker['exchange']):
                            etf_data.append(processed_ticker)
                            logger.debug(f"Found ETF: {processed_ticker['ticker']} from {primary_exchange}")
                
                logger.info(f"ETF page {request_count}, got {len(results)} results. ETFs collected: {len(etf_data)}")
                
                # Check for pagination
                next_url = response.get('next_url')
                if not next_url:
                    break
                    
                # Add delay to respect rate limits
                import time
                time.sleep(12)
                
            else:
                logger.error(f"Invalid ETF response from Polygon.io: {response}")
                break
                
    except Exception as e:
        logger.error(f"Error fetching ETFs from Polygon.io: {e}")
    
    logger.info(f"ETF-specific fetch completed: {len(etf_data)} ETFs from {request_count} API requests")
    if etf_data:
        exchanges = list(set(etf['exchange'] for etf in etf_data if etf.get('exchange')))
        logger.info(f"ETFs found from exchanges: {exchanges}")
    
    return etf_data


def combine_and_deduplicate_tickers(stocks_and_etfs: List[Dict[str, Any]], etfs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Combine ticker data from multiple sources and remove duplicates.
    
    Args:
        stocks_and_etfs: Data from general stocks/ETFs fetch
        etfs: Data from ETF-specific fetch
        
    Returns:
        Combined and deduplicated list of tickers
    """
    # Use a dictionary to deduplicate by ticker symbol
    ticker_dict = {}
    
    # Add stocks and ETFs from general fetch
    for ticker in stocks_and_etfs:
        ticker_dict[ticker['ticker']] = ticker
    
    # Add ETFs from specific fetch (will overwrite if duplicate, ensuring we have latest data)
    for ticker in etfs:
        ticker_dict[ticker['ticker']] = ticker
    
    combined_data = list(ticker_dict.values())
    
    # Count by type for logging
    stocks_count = sum(1 for t in combined_data if t['type'] == 'cs')
    etfs_count = sum(1 for t in combined_data if t['type'] == 'etp')
    
    logger.info(f"Combined ticker data: {stocks_count} stocks, {etfs_count} ETFs, {len(combined_data)} total")
    
    return combined_data


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
        from .models import Tickers
        
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
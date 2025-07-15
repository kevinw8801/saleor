"""
Configurable data source abstraction for Polygon.io integration

This module provides a unified interface that can switch between REST API
and WebSocket data sources based on configuration.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date
import logging
from django.conf import settings

from .clients import PolygonIOClient
from .cache import CachedPolygonClient, PolygonCacheManager
from .websocket_client import get_websocket_manager
from .settings import (
    should_use_websocket, should_use_rest_api, get_fallback_source,
    is_websocket_enabled_for_market, get_data_source_setting
)

logger = logging.getLogger(__name__)


class PolygonDataSourceManager:
    """
    Unified data source manager that can use REST API or WebSocket
    based on configuration and availability.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'POLYGON_IO_API_KEY', None)
        self._rest_client = None
        self._websocket_manager = None
        
        # Initialize based on configuration
        self._init_data_sources()
    
    def _init_data_sources(self):
        """Initialize available data sources based on configuration"""
        # Initialize REST client if enabled
        if should_use_rest_api():
            try:
                polygon_client = PolygonIOClient(self.api_key)
                cache_manager = PolygonCacheManager()
                self._rest_client = CachedPolygonClient(polygon_client, cache_manager)
                logger.info("REST API client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize REST client: {e}")
        
        # Initialize WebSocket manager if enabled
        if get_data_source_setting('ENABLE_WEBSOCKET'):
            try:
                self._websocket_manager = get_websocket_manager()
                logger.info("WebSocket manager initialized")
            except Exception as e:
                logger.error(f"Failed to initialize WebSocket manager: {e}")
    
    @property
    def rest_client(self) -> Optional[CachedPolygonClient]:
        """Get REST API client"""
        return self._rest_client
    
    @property
    def websocket_manager(self):
        """Get WebSocket manager"""
        return self._websocket_manager
    
    def _get_market_type_for_symbol(self, symbol: str) -> str:
        """Determine market type based on symbol format"""
        symbol = symbol.upper()
        
        # Crypto symbols typically end with USD or contain specific patterns
        if any(crypto in symbol for crypto in ['USD', 'BTC', 'ETH', 'USDT']):
            return 'crypto'
        
        # Forex symbols are typically 6 characters (EURUSD, GBPUSD, etc.)
        if len(symbol) == 6 and symbol.isalpha():
            return 'forex'
        
        # Default to stocks
        return 'stocks'
    
    def _should_use_websocket_for_quote(self, symbol: str, market_type: str = None) -> bool:
        """Determine if WebSocket should be used for real-time quotes"""
        if not should_use_websocket():
            return False
        
        if market_type is None:
            market_type = self._get_market_type_for_symbol(symbol)
        
        return is_websocket_enabled_for_market(market_type)
    
    def _try_websocket_quote(self, symbol: str, market_type: str = None) -> Optional[Dict[str, Any]]:
        """Try to get quote from WebSocket data"""
        try:
            if not self._websocket_manager:
                return None
            
            if market_type is None:
                market_type = self._get_market_type_for_symbol(symbol)
            
            # Get cached WebSocket data
            quote_data = self._websocket_manager.get_cached_quote(symbol, market_type)
            if quote_data:
                # Convert WebSocket format to consistent format
                return {
                    'status': 'OK',
                    'results': {
                        'c': quote_data.get('bid'),  # Use bid as current price
                        'b': quote_data.get('bid'),
                        'a': quote_data.get('ask'),
                        'v': quote_data.get('bid_size', 0),
                        't': quote_data.get('timestamp')
                    },
                    'source': 'websocket'
                }
        except Exception as e:
            logger.error(f"Error getting WebSocket quote for {symbol}: {e}")
        
        return None
    
    def _try_rest_quote(self, symbol: str, market_type: str = None) -> Optional[Dict[str, Any]]:
        """Try to get quote from REST API"""
        try:
            if not self._rest_client:
                return None
            
            if market_type is None:
                market_type = self._get_market_type_for_symbol(symbol)
            
            if market_type == 'crypto':
                data = self._rest_client.get_crypto_quote(symbol)
            elif market_type == 'forex':
                data = self._rest_client.get_forex_quote(symbol)
            else:  # stocks
                data = self._rest_client.get_stock_quote(symbol)
            
            if data:
                data['source'] = 'rest'
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting REST quote for {symbol}: {e}")
        
        return None
    
    def get_quote(self, symbol: str, market_type: str = None) -> Optional[Dict[str, Any]]:
        """
        Get real-time quote using configured data source with fallback
        
        Args:
            symbol: Symbol to get quote for
            market_type: 'stocks', 'crypto', or 'forex' (auto-detected if None)
            
        Returns:
            Quote data or None if not available
        """
        if market_type is None:
            market_type = self._get_market_type_for_symbol(symbol)
        
        primary_source = get_data_source_setting('PRIMARY_SOURCE')
        fallback_source = get_fallback_source()
        
        # Try primary source first
        if primary_source == 'websocket':
            data = self._try_websocket_quote(symbol, market_type)
            if data:
                return data
            
            # Fallback to REST if WebSocket fails
            if fallback_source == 'rest':
                logger.debug(f"WebSocket failed for {symbol}, falling back to REST")
                return self._try_rest_quote(symbol, market_type)
        
        else:  # primary_source == 'rest'
            data = self._try_rest_quote(symbol, market_type)
            if data:
                return data
            
            # Fallback to WebSocket if REST fails
            if fallback_source == 'websocket':
                logger.debug(f"REST failed for {symbol}, falling back to WebSocket")
                return self._try_websocket_quote(symbol, market_type)
        
        logger.warning(f"No data source available for {symbol}")
        return None
    
    def get_historical_data(self, symbol: str, timespan: str = 'day', 
                          from_date: Union[str, date] = None,
                          to_date: Union[str, date] = None,
                          limit: int = 100,
                          market_type: str = None) -> Optional[Dict[str, Any]]:
        """
        Get historical data (always uses REST API as WebSocket doesn't provide historical data)
        """
        if not self._rest_client:
            logger.error("REST client not available for historical data")
            return None
        
        try:
            if market_type is None:
                market_type = self._get_market_type_for_symbol(symbol)
            
            if market_type == 'crypto':
                return self._rest_client.get_crypto_bars(symbol, timespan, from_date, to_date, limit)
            elif market_type == 'forex':
                return self._rest_client.get_forex_bars(symbol, timespan, from_date, to_date, limit)
            else:  # stocks
                return self._rest_client.get_stock_bars(symbol, timespan, from_date, to_date, limit)
                
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return None
    
    def get_details(self, symbol: str, market_type: str = None) -> Optional[Dict[str, Any]]:
        """
        Get instrument details (uses REST API)
        """
        if not self._rest_client:
            logger.error("REST client not available for details")
            return None
        
        try:
            if market_type is None:
                market_type = self._get_market_type_for_symbol(symbol)
            
            if market_type == 'crypto':
                return self._rest_client.get_crypto_details(symbol)
            elif market_type == 'forex':
                return self._rest_client.get_forex_details(symbol)
            else:  # stocks
                return self._rest_client.get_stock_details(symbol)
                
        except Exception as e:
            logger.error(f"Error getting details for {symbol}: {e}")
            return None
    
    def get_options_chain(self, underlying_ticker: str, expiration_date: str = None, 
                         option_type: str = None) -> Optional[Dict[str, Any]]:
        """Get options chain (uses REST API)"""
        if not self._rest_client:
            logger.error("REST client not available for options")
            return None
        
        try:
            return self._rest_client.get_options_chain(underlying_ticker, expiration_date, option_type)
        except Exception as e:
            logger.error(f"Error getting options chain for {underlying_ticker}: {e}")
            return None
    
    def get_market_status(self) -> Optional[Dict[str, Any]]:
        """Get market status (uses REST API)"""
        if not self._rest_client:
            logger.error("REST client not available for market status")
            return None
        
        try:
            return self._rest_client.get_market_status()
        except Exception as e:
            logger.error(f"Error getting market status: {e}")
            return None
    
    def search_tickers(self, search_query: str, market: str = None) -> Optional[Dict[str, Any]]:
        """Search tickers (uses REST API)"""
        if not self._rest_client:
            logger.error("REST client not available for search")
            return None
        
        try:
            return self._rest_client.search_tickers(search_query, market)
        except Exception as e:
            logger.error(f"Error searching tickers: {e}")
            return None
    
    def subscribe_to_real_time_data(self, symbols: List[str], market_type: str = 'stocks', 
                                   data_type: str = 'quotes') -> bool:
        """
        Subscribe to real-time data via WebSocket
        
        Args:
            symbols: List of symbols to subscribe to
            market_type: 'stocks', 'crypto', or 'forex'
            data_type: 'quotes' or 'trades'
            
        Returns:
            True if subscription successful, False otherwise
        """
        if not self._websocket_manager:
            logger.error("WebSocket manager not available")
            return False
        
        if not is_websocket_enabled_for_market(market_type):
            logger.error(f"WebSocket not enabled for {market_type}")
            return False
        
        try:
            # Start WebSocket manager if not running
            if not self._websocket_manager.is_running:
                self._websocket_manager.start()
            
            # Subscribe based on data type
            if data_type == 'quotes':
                return self._websocket_manager.subscribe_quotes(symbols, market_type)
            elif data_type == 'trades':
                return self._websocket_manager.subscribe_trades(symbols, market_type)
            else:
                logger.error(f"Invalid data type: {data_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error subscribing to real-time data: {e}")
            return False
    
    def get_data_source_status(self) -> Dict[str, Any]:
        """Get status of available data sources"""
        status = {
            'rest_api': {
                'available': self._rest_client is not None,
                'enabled': should_use_rest_api()
            },
            'websocket': {
                'available': self._websocket_manager is not None,
                'enabled': get_data_source_setting('ENABLE_WEBSOCKET'),
                'running': self._websocket_manager.is_running if self._websocket_manager else False
            },
            'primary_source': get_data_source_setting('PRIMARY_SOURCE'),
            'fallback_source': get_fallback_source()
        }
        
        return status


# Global data source manager instance
_data_source_manager = None

def get_data_source_manager() -> PolygonDataSourceManager:
    """Get global data source manager instance"""
    global _data_source_manager
    if _data_source_manager is None:
        api_key = getattr(settings, 'POLYGON_IO_API_KEY', None)
        _data_source_manager = PolygonDataSourceManager(api_key)
    return _data_source_manager
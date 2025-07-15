from datetime import datetime, timedelta
from typing import Any, Optional, Dict
from django.core.cache import cache
from django.utils import timezone
from .models import MarketDataCache
import json
import hashlib


class PolygonCacheManager:
    """Enhanced caching manager for Polygon.io data with database fallback"""
    
    # Cache timeout configurations (in seconds)
    CACHE_TIMEOUTS = {
        'quote': 60,           # Real-time quotes: 1 minute
        'bars': 300,           # Price bars: 5 minutes
        'details': 3600,       # Instrument details: 1 hour
        'options': 1800,       # Options data: 30 minutes
        'market_status': 300,  # Market status: 5 minutes
        'search': 1800,        # Search results: 30 minutes
        'default': 300         # Default: 5 minutes
    }
    
    def __init__(self):
        self.redis_cache = cache
    
    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate a consistent cache key from parameters"""
        key_data = f"{prefix}:{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_timeout(self, data_type: str) -> int:
        """Get cache timeout for specific data type"""
        return self.CACHE_TIMEOUTS.get(data_type, self.CACHE_TIMEOUTS['default'])
    
    def get(self, cache_key: str, data_type: str = 'default') -> Optional[Dict[str, Any]]:
        """
        Get data from cache with Redis first, database fallback
        """
        # Try Redis cache first
        cached_data = self.redis_cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Fallback to database cache
        try:
            db_cache = MarketDataCache.objects.get(cache_key=cache_key)
            if not db_cache.is_expired():
                # Restore to Redis cache
                timeout = self._get_timeout(data_type)
                self.redis_cache.set(cache_key, db_cache.data, timeout)
                return db_cache.data
            else:
                # Clean up expired cache
                db_cache.delete()
        except MarketDataCache.DoesNotExist:
            pass
        
        return None
    
    def set(self, cache_key: str, data: Dict[str, Any], data_type: str = 'default') -> None:
        """
        Set data in both Redis and database cache
        """
        timeout = self._get_timeout(data_type)
        expires_at = timezone.now() + timedelta(seconds=timeout)
        
        # Set in Redis cache
        self.redis_cache.set(cache_key, data, timeout)
        
        # Set in database cache (for persistence)
        MarketDataCache.objects.update_or_create(
            cache_key=cache_key,
            defaults={
                'data': data,
                'expires_at': expires_at
            }
        )
    
    def invalidate(self, cache_key: str) -> None:
        """Remove data from both caches"""
        self.redis_cache.delete(cache_key)
        MarketDataCache.objects.filter(cache_key=cache_key).delete()
    
    def clear_expired(self) -> int:
        """Clear all expired cache entries from database"""
        count = MarketDataCache.objects.filter(expires_at__lt=timezone.now()).count()
        MarketDataCache.objects.filter(expires_at__lt=timezone.now()).delete()
        return count
    
    def get_stock_quote_key(self, symbol: str) -> str:
        """Generate cache key for stock quote"""
        return self._generate_cache_key('stock_quote', symbol=symbol)
    
    def get_stock_bars_key(self, symbol: str, timespan: str, from_date: str, to_date: str, limit: int) -> str:
        """Generate cache key for stock bars"""
        return self._generate_cache_key(
            'stock_bars', 
            symbol=symbol, 
            timespan=timespan, 
            from_date=from_date, 
            to_date=to_date, 
            limit=limit
        )
    
    def get_stock_details_key(self, symbol: str) -> str:
        """Generate cache key for stock details"""
        return self._generate_cache_key('stock_details', symbol=symbol)
    
    def get_options_chain_key(self, underlying_ticker: str, expiration_date: str = None, option_type: str = None) -> str:
        """Generate cache key for options chain"""
        return self._generate_cache_key(
            'options_chain',
            underlying_ticker=underlying_ticker,
            expiration_date=expiration_date or '',
            option_type=option_type or ''
        )
    
    def get_option_quote_key(self, option_ticker: str) -> str:
        """Generate cache key for option quote"""
        return self._generate_cache_key('option_quote', option_ticker=option_ticker)
    
    def get_crypto_quote_key(self, symbol: str) -> str:
        """Generate cache key for crypto quote"""
        return self._generate_cache_key('crypto_quote', symbol=symbol)
    
    def get_crypto_bars_key(self, symbol: str, timespan: str, from_date: str, to_date: str, limit: int) -> str:
        """Generate cache key for crypto bars"""
        return self._generate_cache_key(
            'crypto_bars',
            symbol=symbol,
            timespan=timespan,
            from_date=from_date,
            to_date=to_date,
            limit=limit
        )
    
    def get_crypto_details_key(self, symbol: str) -> str:
        """Generate cache key for crypto details"""
        return self._generate_cache_key('crypto_details', symbol=symbol)
    
    def get_forex_quote_key(self, symbol: str) -> str:
        """Generate cache key for forex quote"""
        return self._generate_cache_key('forex_quote', symbol=symbol)
    
    def get_forex_bars_key(self, symbol: str, timespan: str, from_date: str, to_date: str, limit: int) -> str:
        """Generate cache key for forex bars"""
        return self._generate_cache_key(
            'forex_bars',
            symbol=symbol,
            timespan=timespan,
            from_date=from_date,
            to_date=to_date,
            limit=limit
        )
    
    def get_forex_details_key(self, symbol: str) -> str:
        """Generate cache key for forex details"""
        return self._generate_cache_key('forex_details', symbol=symbol)
    
    def get_market_status_key(self) -> str:
        """Generate cache key for market status"""
        return self._generate_cache_key('market_status')
    
    def get_search_key(self, search_query: str, market: str = None) -> str:
        """Generate cache key for search results"""
        return self._generate_cache_key(
            'search',
            query=search_query,
            market=market or ''
        )


class CachedPolygonClient:
    """Wrapper around PolygonIOClient with enhanced caching"""
    
    def __init__(self, polygon_client, cache_manager: PolygonCacheManager = None):
        self.client = polygon_client
        self.cache = cache_manager or PolygonCacheManager()
    
    def get_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """Get stock quote with caching"""
        cache_key = self.cache.get_stock_quote_key(symbol)
        cached_data = self.cache.get(cache_key, 'quote')
        
        if cached_data is not None:
            return cached_data
        
        data = self.client.get_stock_quote(symbol)
        self.cache.set(cache_key, data, 'quote')
        return data
    
    def get_stock_bars(self, symbol: str, timespan: str = "day", 
                      from_date: str = None, to_date: str = None, limit: int = 100) -> Dict[str, Any]:
        """Get stock bars with caching"""
        cache_key = self.cache.get_stock_bars_key(symbol, timespan, from_date or '', to_date or '', limit)
        cached_data = self.cache.get(cache_key, 'bars')
        
        if cached_data is not None:
            return cached_data
        
        data = self.client.get_stock_bars(symbol, timespan, from_date, to_date, limit)
        self.cache.set(cache_key, data, 'bars')
        return data
    
    def get_stock_details(self, symbol: str) -> Dict[str, Any]:
        """Get stock details with caching"""
        cache_key = self.cache.get_stock_details_key(symbol)
        cached_data = self.cache.get(cache_key, 'details')
        
        if cached_data is not None:
            return cached_data
        
        data = self.client.get_stock_details(symbol)
        self.cache.set(cache_key, data, 'details')
        return data
    
    def get_options_chain(self, underlying_ticker: str, expiration_date: str = None, option_type: str = None) -> Dict[str, Any]:
        """Get options chain with caching"""
        cache_key = self.cache.get_options_chain_key(underlying_ticker, expiration_date, option_type)
        cached_data = self.cache.get(cache_key, 'options')
        
        if cached_data is not None:
            return cached_data
        
        data = self.client.get_options_chain(underlying_ticker, expiration_date, option_type)
        self.cache.set(cache_key, data, 'options')
        return data
    
    def get_option_quote(self, option_ticker: str) -> Dict[str, Any]:
        """Get option quote with caching"""
        cache_key = self.cache.get_option_quote_key(option_ticker)
        cached_data = self.cache.get(cache_key, 'quote')
        
        if cached_data is not None:
            return cached_data
        
        data = self.client.get_option_quote(option_ticker)
        self.cache.set(cache_key, data, 'quote')
        return data
    
    def get_crypto_quote(self, symbol: str) -> Dict[str, Any]:
        """Get crypto quote with caching"""
        cache_key = self.cache.get_crypto_quote_key(symbol)
        cached_data = self.cache.get(cache_key, 'quote')
        
        if cached_data is not None:
            return cached_data
        
        data = self.client.get_crypto_quote(symbol)
        self.cache.set(cache_key, data, 'quote')
        return data
    
    def get_crypto_bars(self, symbol: str, timespan: str = "hour",
                       from_date: str = None, to_date: str = None, limit: int = 100) -> Dict[str, Any]:
        """Get crypto bars with caching"""
        cache_key = self.cache.get_crypto_bars_key(symbol, timespan, from_date or '', to_date or '', limit)
        cached_data = self.cache.get(cache_key, 'bars')
        
        if cached_data is not None:
            return cached_data
        
        data = self.client.get_crypto_bars(symbol, timespan, from_date, to_date, limit)
        self.cache.set(cache_key, data, 'bars')
        return data
    
    def get_crypto_details(self, symbol: str) -> Dict[str, Any]:
        """Get crypto details with caching"""
        cache_key = self.cache.get_crypto_details_key(symbol)
        cached_data = self.cache.get(cache_key, 'details')
        
        if cached_data is not None:
            return cached_data
        
        data = self.client.get_crypto_details(symbol)
        self.cache.set(cache_key, data, 'details')
        return data
    
    def get_forex_quote(self, symbol: str) -> Dict[str, Any]:
        """Get forex quote with caching"""
        cache_key = self.cache.get_forex_quote_key(symbol)
        cached_data = self.cache.get(cache_key, 'quote')
        
        if cached_data is not None:
            return cached_data
        
        data = self.client.get_forex_quote(symbol)
        self.cache.set(cache_key, data, 'quote')
        return data
    
    def get_forex_bars(self, symbol: str, timespan: str = "hour",
                      from_date: str = None, to_date: str = None, limit: int = 100) -> Dict[str, Any]:
        """Get forex bars with caching"""
        cache_key = self.cache.get_forex_bars_key(symbol, timespan, from_date or '', to_date or '', limit)
        cached_data = self.cache.get(cache_key, 'bars')
        
        if cached_data is not None:
            return cached_data
        
        data = self.client.get_forex_bars(symbol, timespan, from_date, to_date, limit)
        self.cache.set(cache_key, data, 'bars')
        return data
    
    def get_forex_details(self, symbol: str) -> Dict[str, Any]:
        """Get forex details with caching"""
        cache_key = self.cache.get_forex_details_key(symbol)
        cached_data = self.cache.get(cache_key, 'details')
        
        if cached_data is not None:
            return cached_data
        
        data = self.client.get_forex_details(symbol)
        self.cache.set(cache_key, data, 'details')
        return data
    
    def get_market_status(self) -> Dict[str, Any]:
        """Get market status with caching"""
        cache_key = self.cache.get_market_status_key()
        cached_data = self.cache.get(cache_key, 'market_status')
        
        if cached_data is not None:
            return cached_data
        
        data = self.client.get_market_status()
        self.cache.set(cache_key, data, 'market_status')
        return data
    
    def search_tickers(self, search_query: str, market: str = None) -> Dict[str, Any]:
        """Search tickers with caching"""
        cache_key = self.cache.get_search_key(search_query, market)
        cached_data = self.cache.get(cache_key, 'search')
        
        if cached_data is not None:
            return cached_data
        
        data = self.client.search_tickers(search_query, market)
        self.cache.set(cache_key, data, 'search')
        return data
import requests
import time
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal
from django.conf import settings
from django.core.cache import cache


class PolygonIOClient:
    """Client for Polygon.io financial data API"""
    
    BASE_URL = "https://api.polygon.io"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'POLYGON_IO_API_KEY', None)
        if not self.api_key:
            raise ValueError("Polygon.io API key is required")
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """Make HTTP request to Polygon.io API with rate limiting and error handling"""
        url = f"{self.BASE_URL}{endpoint}"
        params = params or {}
        params['apikey'] = self.api_key
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'ERROR':
                raise Exception(f"Polygon.io API Error: {data.get('error', 'Unknown error')}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"API request error: {str(e)}")
    
    def _get_cached_or_fetch(self, cache_key: str, fetch_func, cache_timeout: int = 300):
        """Get data from cache or fetch from API if not cached"""
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        
        data = fetch_func()
        cache.set(cache_key, data, cache_timeout)
        return data
    
    # Stock Data Methods
    def get_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time stock quote"""
        cache_key = f"polygon_stock_quote_{symbol}"
        
        def fetch():
            endpoint = f"/v2/last/trade/{symbol}"
            return self._make_request(endpoint)
        
        return self._get_cached_or_fetch(cache_key, fetch, cache_timeout=60)
    
    def get_stock_bars(self, symbol: str, timespan: str = "day", 
                      from_date: Union[str, date] = None, 
                      to_date: Union[str, date] = None,
                      limit: int = 100) -> Dict[str, Any]:
        """Get stock aggregates/bars"""
        cache_key = f"polygon_stock_bars_{symbol}_{timespan}_{from_date}_{to_date}_{limit}"
        
        def fetch():
            if isinstance(from_date, date):
                from_date_str = from_date.strftime('%Y-%m-%d')
            else:
                from_date_str = from_date or "2023-01-01"
                
            if isinstance(to_date, date):
                to_date_str = to_date.strftime('%Y-%m-%d')
            else:
                to_date_str = to_date or datetime.now().strftime('%Y-%m-%d')
            
            endpoint = f"/v2/aggs/ticker/{symbol}/range/1/{timespan}/{from_date_str}/{to_date_str}"
            params = {'limit': limit}
            return self._make_request(endpoint, params)
        
        return self._get_cached_or_fetch(cache_key, fetch, cache_timeout=300)
    
    def get_stock_details(self, symbol: str) -> Dict[str, Any]:
        """Get stock ticker details"""
        cache_key = f"polygon_stock_details_{symbol}"
        
        def fetch():
            endpoint = f"/v3/reference/tickers/{symbol}"
            return self._make_request(endpoint)
        
        return self._get_cached_or_fetch(cache_key, fetch, cache_timeout=3600)
    
    # Options Data Methods
    def get_options_chain(self, underlying_ticker: str, 
                         expiration_date: Union[str, date] = None,
                         option_type: str = None) -> Dict[str, Any]:
        """Get options chain for an underlying asset"""
        cache_key = f"polygon_options_{underlying_ticker}_{expiration_date}_{option_type}"
        
        def fetch():
            endpoint = "/v3/reference/options/contracts"
            params = {
                'underlying_ticker': underlying_ticker,
                'limit': 1000
            }
            
            if expiration_date:
                if isinstance(expiration_date, date):
                    params['expiration_date'] = expiration_date.strftime('%Y-%m-%d')
                else:
                    params['expiration_date'] = expiration_date
            
            if option_type:
                params['contract_type'] = option_type
            
            return self._make_request(endpoint, params)
        
        return self._get_cached_or_fetch(cache_key, fetch, cache_timeout=1800)
    
    def get_option_quote(self, option_ticker: str) -> Dict[str, Any]:
        """Get option quote"""
        cache_key = f"polygon_option_quote_{option_ticker}"
        
        def fetch():
            endpoint = f"/v2/last/nbbo/{option_ticker}"
            return self._make_request(endpoint)
        
        return self._get_cached_or_fetch(cache_key, fetch, cache_timeout=60)
    
    # Crypto Data Methods
    def get_crypto_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time crypto quote"""
        cache_key = f"polygon_crypto_quote_{symbol}"
        
        def fetch():
            endpoint = f"/v2/last/crypto/{symbol}"
            return self._make_request(endpoint)
        
        return self._get_cached_or_fetch(cache_key, fetch, cache_timeout=30)
    
    def get_crypto_bars(self, symbol: str, timespan: str = "hour",
                       from_date: Union[str, date] = None,
                       to_date: Union[str, date] = None,
                       limit: int = 100) -> Dict[str, Any]:
        """Get crypto aggregates/bars"""
        cache_key = f"polygon_crypto_bars_{symbol}_{timespan}_{from_date}_{to_date}_{limit}"
        
        def fetch():
            if isinstance(from_date, date):
                from_date_str = from_date.strftime('%Y-%m-%d')
            else:
                from_date_str = from_date or "2023-01-01"
                
            if isinstance(to_date, date):
                to_date_str = to_date.strftime('%Y-%m-%d')
            else:
                to_date_str = to_date or datetime.now().strftime('%Y-%m-%d')
            
            endpoint = f"/v2/aggs/ticker/X:{symbol}/range/1/{timespan}/{from_date_str}/{to_date_str}"
            params = {'limit': limit}
            return self._make_request(endpoint, params)
        
        return self._get_cached_or_fetch(cache_key, fetch, cache_timeout=300)
    
    def get_crypto_details(self, symbol: str) -> Dict[str, Any]:
        """Get crypto ticker details"""
        cache_key = f"polygon_crypto_details_{symbol}"
        
        def fetch():
            endpoint = f"/v3/reference/tickers/X:{symbol}"
            return self._make_request(endpoint)
        
        return self._get_cached_or_fetch(cache_key, fetch, cache_timeout=3600)
    
    # Forex Data Methods
    def get_forex_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time forex quote"""
        cache_key = f"polygon_forex_quote_{symbol}"
        
        def fetch():
            endpoint = f"/v2/last/forex/{symbol}"
            return self._make_request(endpoint)
        
        return self._get_cached_or_fetch(cache_key, fetch, cache_timeout=60)
    
    def get_forex_bars(self, symbol: str, timespan: str = "hour",
                      from_date: Union[str, date] = None,
                      to_date: Union[str, date] = None,
                      limit: int = 100) -> Dict[str, Any]:
        """Get forex aggregates/bars"""
        cache_key = f"polygon_forex_bars_{symbol}_{timespan}_{from_date}_{to_date}_{limit}"
        
        def fetch():
            if isinstance(from_date, date):
                from_date_str = from_date.strftime('%Y-%m-%d')
            else:
                from_date_str = from_date or "2023-01-01"
                
            if isinstance(to_date, date):
                to_date_str = to_date.strftime('%Y-%m-%d')
            else:
                to_date_str = to_date or datetime.now().strftime('%Y-%m-%d')
            
            endpoint = f"/v2/aggs/ticker/C:{symbol}/range/1/{timespan}/{from_date_str}/{to_date_str}"
            params = {'limit': limit}
            return self._make_request(endpoint, params)
        
        return self._get_cached_or_fetch(cache_key, fetch, cache_timeout=300)
    
    def get_forex_details(self, symbol: str) -> Dict[str, Any]:
        """Get forex ticker details"""
        cache_key = f"polygon_forex_details_{symbol}"
        
        def fetch():
            endpoint = f"/v3/reference/tickers/C:{symbol}"
            return self._make_request(endpoint)
        
        return self._get_cached_or_fetch(cache_key, fetch, cache_timeout=3600)
    
    # Market Status and Reference Data
    def get_market_status(self) -> Dict[str, Any]:
        """Get current market status"""
        cache_key = "polygon_market_status"
        
        def fetch():
            endpoint = "/v1/marketstatus/now"
            return self._make_request(endpoint)
        
        return self._get_cached_or_fetch(cache_key, fetch, cache_timeout=300)
    
    def search_tickers(self, search_query: str, market: str = None) -> Dict[str, Any]:
        """Search for tickers"""
        cache_key = f"polygon_search_{search_query}_{market}"
        
        def fetch():
            endpoint = "/v3/reference/tickers"
            params = {
                'search': search_query,
                'limit': 100
            }
            
            if market:
                params['market'] = market
            
            return self._make_request(endpoint, params)
        
        return self._get_cached_or_fetch(cache_key, fetch, cache_timeout=1800)
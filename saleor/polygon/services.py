"""
Service layer for Polygon.io integration with Saleor

This module provides high-level service functions that other parts of Saleor
can use to interact with financial market data from Polygon.io.
"""

from typing import Dict, List, Optional, Any
from django.conf import settings
from .clients import PolygonIOClient
from .cache import CachedPolygonClient, PolygonCacheManager
from .models import FinancialInstrument, StockData, OptionData, CryptoData, ForexData


class PolygonFinancialDataService:
    """
    High-level service for accessing financial market data
    
    This service provides a clean interface for other Saleor components
    to access stock, options, crypto, and forex data from Polygon.io.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'POLYGON_IO_API_KEY', None)
        self._client = None
    
    @property
    def client(self) -> CachedPolygonClient:
        """Lazy-loaded cached Polygon.io client"""
        if self._client is None:
            if not self.api_key:
                raise ValueError("Polygon.io API key not configured")
            
            polygon_client = PolygonIOClient(self.api_key)
            cache_manager = PolygonCacheManager()
            self._client = CachedPolygonClient(polygon_client, cache_manager)
        
        return self._client
    
    # Stock data methods
    def get_stock_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current stock price"""
        try:
            data = self.client.get_stock_quote(symbol.upper())
            if data and data.get('status') == 'OK':
                return {
                    'symbol': symbol.upper(),
                    'price': data.get('results', {}).get('c'),  # close/current price
                    'bid': data.get('results', {}).get('b'),
                    'ask': data.get('results', {}).get('a'),
                    'volume': data.get('results', {}).get('v'),
                    'timestamp': data.get('results', {}).get('t')
                }
        except Exception:
            pass
        return None
    
    def get_stock_historical_data(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get historical stock data for specified number of days"""
        try:
            data = self.client.get_stock_bars(symbol.upper(), timespan='day', limit=days)
            if data and data.get('status') == 'OK':
                results = data.get('results', [])
                return [
                    {
                        'symbol': symbol.upper(),
                        'date': result.get('t'),
                        'open': result.get('o'),
                        'high': result.get('h'),
                        'low': result.get('l'),
                        'close': result.get('c'),
                        'volume': result.get('v'),
                        'vwap': result.get('vw')
                    }
                    for result in results
                ]
        except Exception:
            pass
        return []
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed stock information"""
        try:
            data = self.client.get_stock_details(symbol.upper())
            if data and data.get('status') == 'OK':
                results = data.get('results', {})
                return {
                    'symbol': symbol.upper(),
                    'name': results.get('name'),
                    'description': results.get('description'),
                    'market': results.get('market'),
                    'locale': results.get('locale'),
                    'currency_name': results.get('currency_name'),
                    'market_cap': results.get('market_cap'),
                    'share_class_shares_outstanding': results.get('share_class_shares_outstanding'),
                    'sic_description': results.get('sic_description'),
                    'homepage_url': results.get('homepage_url')
                }
        except Exception:
            pass
        return None
    
    # Crypto data methods
    def get_crypto_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current cryptocurrency price"""
        try:
            data = self.client.get_crypto_quote(symbol.upper())
            if data and data.get('status') == 'OK':
                return {
                    'symbol': symbol.upper(),
                    'price': data.get('results', {}).get('c'),
                    'bid': data.get('results', {}).get('b'),
                    'ask': data.get('results', {}).get('a'),
                    'volume': data.get('results', {}).get('v'),
                    'timestamp': data.get('results', {}).get('t')
                }
        except Exception:
            pass
        return None
    
    def get_crypto_historical_data(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get historical crypto data"""
        try:
            data = self.client.get_crypto_bars(symbol.upper(), timespan='day', limit=days)
            if data and data.get('status') == 'OK':
                results = data.get('results', [])
                return [
                    {
                        'symbol': symbol.upper(),
                        'date': result.get('t'),
                        'open': result.get('o'),
                        'high': result.get('h'),
                        'low': result.get('l'),
                        'close': result.get('c'),
                        'volume': result.get('v'),
                        'vwap': result.get('vw')
                    }
                    for result in results
                ]
        except Exception:
            pass
        return []
    
    # Forex data methods
    def get_forex_rate(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current forex exchange rate"""
        try:
            data = self.client.get_forex_quote(symbol.upper())
            if data and data.get('status') == 'OK':
                return {
                    'symbol': symbol.upper(),
                    'rate': data.get('results', {}).get('c'),
                    'bid': data.get('results', {}).get('b'),
                    'ask': data.get('results', {}).get('a'),
                    'timestamp': data.get('results', {}).get('t')
                }
        except Exception:
            pass
        return None
    
    def get_forex_historical_data(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get historical forex data"""
        try:
            data = self.client.get_forex_bars(symbol.upper(), timespan='day', limit=days)
            if data and data.get('status') == 'OK':
                results = data.get('results', [])
                return [
                    {
                        'symbol': symbol.upper(),
                        'date': result.get('t'),
                        'open': result.get('o'),
                        'high': result.get('h'),
                        'low': result.get('l'),
                        'close': result.get('c'),
                        'volume': result.get('v')
                    }
                    for result in results
                ]
        except Exception:
            pass
        return []
    
    # Options data methods
    def get_options_chain(self, underlying_symbol: str, expiration_date: str = None) -> List[Dict[str, Any]]:
        """Get options chain for underlying asset"""
        try:
            data = self.client.get_options_chain(underlying_symbol.upper(), expiration_date)
            if data and data.get('status') == 'OK':
                results = data.get('results', [])
                return [
                    {
                        'option_ticker': result.get('ticker'),
                        'underlying_ticker': result.get('underlying_ticker'),
                        'contract_type': result.get('contract_type'),
                        'strike_price': result.get('strike_price'),
                        'expiration_date': result.get('expiration_date'),
                        'exercise_style': result.get('exercise_style'),
                        'shares_per_contract': result.get('shares_per_contract')
                    }
                    for result in results
                ]
        except Exception:
            pass
        return []
    
    def get_option_price(self, option_ticker: str) -> Optional[Dict[str, Any]]:
        """Get current option price"""
        try:
            data = self.client.get_option_quote(option_ticker.upper())
            if data and data.get('status') == 'OK':
                return {
                    'option_ticker': option_ticker.upper(),
                    'bid': data.get('results', {}).get('b'),
                    'ask': data.get('results', {}).get('a'),
                    'last': data.get('results', {}).get('c'),
                    'volume': data.get('results', {}).get('v'),
                    'timestamp': data.get('results', {}).get('t')
                }
        except Exception:
            pass
        return None
    
    # Market status and search
    def get_market_status(self) -> Optional[Dict[str, Any]]:
        """Get current market status"""
        try:
            data = self.client.get_market_status()
            if data and data.get('status') == 'OK':
                return data.get('results', {})
        except Exception:
            pass
        return None
    
    def search_instruments(self, query: str, market: str = None) -> List[Dict[str, Any]]:
        """Search for financial instruments"""
        try:
            data = self.client.search_tickers(query, market)
            if data and data.get('status') == 'OK':
                results = data.get('results', [])
                return [
                    {
                        'ticker': result.get('ticker'),
                        'name': result.get('name'),
                        'market': result.get('market'),
                        'locale': result.get('locale'),
                        'currency_name': result.get('currency_name'),
                        'type': result.get('type')
                    }
                    for result in results
                ]
        except Exception:
            pass
        return []
    
    # Convenience methods for common use cases
    def get_portfolio_values(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """Get current prices for a list of symbols"""
        values = {}
        for symbol in symbols:
            price_data = self.get_stock_price(symbol)
            values[symbol] = price_data.get('price') if price_data else None
        return values
    
    def get_currency_rates(self, base_currency: str, target_currencies: List[str]) -> Dict[str, Optional[float]]:
        """Get exchange rates from base currency to target currencies"""
        rates = {}
        for target in target_currencies:
            symbol = f"{base_currency}{target}"
            rate_data = self.get_forex_rate(symbol)
            rates[target] = rate_data.get('rate') if rate_data else None
        return rates
    
    def validate_symbol(self, symbol: str, instrument_type: str = None) -> bool:
        """Validate if a symbol exists and is tradeable"""
        try:
            results = self.search_instruments(symbol)
            if results:
                for result in results:
                    if result.get('ticker', '').upper() == symbol.upper():
                        if instrument_type:
                            return result.get('type', '').upper() == instrument_type.upper()
                        return True
        except Exception:
            pass
        return False


# Global service instance for easy access
polygon_service = PolygonFinancialDataService()


# Convenience functions for direct use in other Saleor components
def get_stock_price(symbol: str) -> Optional[float]:
    """Get current stock price (simplified interface)"""
    data = polygon_service.get_stock_price(symbol)
    return data.get('price') if data else None


def get_crypto_price(symbol: str) -> Optional[float]:
    """Get current crypto price (simplified interface)"""
    data = polygon_service.get_crypto_price(symbol)
    return data.get('price') if data else None


def get_forex_rate(symbol: str) -> Optional[float]:
    """Get current forex rate (simplified interface)"""
    data = polygon_service.get_forex_rate(symbol)
    return data.get('rate') if data else None


def get_market_open_status() -> bool:
    """Check if market is currently open"""
    status = polygon_service.get_market_status()
    if status:
        return status.get('market') == 'open'
    return False
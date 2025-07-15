"""
Configuration settings for Polygon integration

Add these settings to your Django settings.py file:

# Polygon.io API Configuration
POLYGON_IO_API_KEY = os.environ.get('POLYGON_IO_API_KEY', None)

# Cache settings for financial data
POLYGON_CACHE_SETTINGS = {
    'QUOTE_CACHE_TIMEOUT': 60,           # Real-time quotes: 1 minute
    'BARS_CACHE_TIMEOUT': 300,           # Price bars: 5 minutes  
    'DETAILS_CACHE_TIMEOUT': 3600,       # Instrument details: 1 hour
    'OPTIONS_CACHE_TIMEOUT': 1800,       # Options data: 30 minutes
    'MARKET_STATUS_CACHE_TIMEOUT': 300,  # Market status: 5 minutes
    'SEARCH_CACHE_TIMEOUT': 1800,        # Search results: 30 minutes
    'DEFAULT_CACHE_TIMEOUT': 300         # Default: 5 minutes
}

# Rate limiting settings
POLYGON_RATE_LIMIT = {
    'REQUESTS_PER_MINUTE': 5,    # Free tier limit
    'REQUESTS_PER_DAY': 1000,    # Free tier limit
    'ENABLE_RATE_LIMITING': True
}

# Database settings for financial data storage
POLYGON_DATA_RETENTION = {
    'KEEP_STOCK_DATA_DAYS': 365,     # Keep stock data for 1 year
    'KEEP_CRYPTO_DATA_DAYS': 180,    # Keep crypto data for 6 months
    'KEEP_FOREX_DATA_DAYS': 90,      # Keep forex data for 3 months
    'KEEP_OPTIONS_DATA_DAYS': 30,    # Keep options data for 1 month
    'KEEP_CACHE_DATA_DAYS': 7        # Keep cache data for 1 week
}

# Default symbols to track
POLYGON_DEFAULT_SYMBOLS = {
    'STOCKS': ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN'],
    'CRYPTO': ['BTCUSD', 'ETHUSD', 'ADAUSD', 'DOTUSD'],
    'FOREX': ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD']
}

# Data source configuration
POLYGON_DATA_SOURCE = {
    'PRIMARY_SOURCE': 'rest',        # 'rest' or 'websocket'
    'FALLBACK_SOURCE': 'rest',       # Fallback if primary fails
    'ENABLE_WEBSOCKET': True,        # Enable WebSocket functionality
    'ENABLE_REST_API': True,         # Enable REST API functionality
    'WEBSOCKET_AUTO_RECONNECT': True,
    'WEBSOCKET_RECONNECT_DELAY': 5,  # seconds
    'WEBSOCKET_MAX_RECONNECT_ATTEMPTS': 10
}

# WebSocket configuration
POLYGON_WEBSOCKET_SETTINGS = {
    'ENABLE_STOCKS_WS': True,
    'ENABLE_CRYPTO_WS': True,
    'ENABLE_FOREX_WS': True,
    'AUTO_SUBSCRIBE_DEFAULT_SYMBOLS': True,
    'STORE_WEBSOCKET_DATA': False,   # Store real-time data in database
    'WEBSOCKET_BUFFER_SIZE': 1000,   # Buffer size for real-time data
}

# Features configuration
POLYGON_FEATURES = {
    'ENABLE_STOCK_DATA': True,
    'ENABLE_CRYPTO_DATA': True,
    'ENABLE_FOREX_DATA': True,
    'ENABLE_OPTIONS_DATA': True,
    'ENABLE_REAL_TIME_QUOTES': True,
    'ENABLE_HISTORICAL_DATA': True,
    'ENABLE_DATA_PERSISTENCE': True
}
"""

import os
from django.conf import settings

# Default configuration values
DEFAULT_POLYGON_SETTINGS = {
    'POLYGON_IO_API_KEY': None,
    'POLYGON_CACHE_SETTINGS': {
        'QUOTE_CACHE_TIMEOUT': 60,
        'BARS_CACHE_TIMEOUT': 300,
        'DETAILS_CACHE_TIMEOUT': 3600,
        'OPTIONS_CACHE_TIMEOUT': 1800,
        'MARKET_STATUS_CACHE_TIMEOUT': 300,
        'SEARCH_CACHE_TIMEOUT': 1800,
        'DEFAULT_CACHE_TIMEOUT': 300
    },
    'POLYGON_RATE_LIMIT': {
        'REQUESTS_PER_MINUTE': 5,
        'REQUESTS_PER_DAY': 1000,
        'ENABLE_RATE_LIMITING': True
    },
    'POLYGON_DATA_RETENTION': {
        'KEEP_STOCK_DATA_DAYS': 365,
        'KEEP_CRYPTO_DATA_DAYS': 180,
        'KEEP_FOREX_DATA_DAYS': 90,
        'KEEP_OPTIONS_DATA_DAYS': 30,
        'KEEP_CACHE_DATA_DAYS': 7
    },
    'POLYGON_DEFAULT_SYMBOLS': {
        'STOCKS': ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN'],
        'CRYPTO': ['BTCUSD', 'ETHUSD', 'ADAUSD', 'DOTUSD'],
        'FOREX': ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD']
    },
    'POLYGON_DATA_SOURCE': {
        'PRIMARY_SOURCE': 'rest',
        'FALLBACK_SOURCE': 'rest',
        'ENABLE_WEBSOCKET': True,
        'ENABLE_REST_API': True,
        'WEBSOCKET_AUTO_RECONNECT': True,
        'WEBSOCKET_RECONNECT_DELAY': 5,
        'WEBSOCKET_MAX_RECONNECT_ATTEMPTS': 10
    },
    'POLYGON_WEBSOCKET_SETTINGS': {
        'ENABLE_STOCKS_WS': True,
        'ENABLE_CRYPTO_WS': True,
        'ENABLE_FOREX_WS': True,
        'AUTO_SUBSCRIBE_DEFAULT_SYMBOLS': True,
        'STORE_WEBSOCKET_DATA': False,
        'WEBSOCKET_BUFFER_SIZE': 1000,
    },
    'POLYGON_FEATURES': {
        'ENABLE_STOCK_DATA': True,
        'ENABLE_CRYPTO_DATA': True,
        'ENABLE_FOREX_DATA': True,
        'ENABLE_OPTIONS_DATA': True,
        'ENABLE_REAL_TIME_QUOTES': True,
        'ENABLE_HISTORICAL_DATA': True,
        'ENABLE_DATA_PERSISTENCE': True
    }
}


def get_polygon_setting(setting_name: str, default_value=None):
    """Get a polygon-specific setting with fallback to defaults"""
    return getattr(settings, setting_name, DEFAULT_POLYGON_SETTINGS.get(setting_name, default_value))


def get_api_key():
    """Get Polygon.io API key from settings or environment"""
    return get_polygon_setting('POLYGON_IO_API_KEY') or os.environ.get('POLYGON_IO_API_KEY')


def get_cache_timeout(data_type: str):
    """Get cache timeout for specific data type"""
    cache_settings = get_polygon_setting('POLYGON_CACHE_SETTINGS', {})
    timeout_key = f"{data_type.upper()}_CACHE_TIMEOUT"
    return cache_settings.get(timeout_key, cache_settings.get('DEFAULT_CACHE_TIMEOUT', 300))


def is_feature_enabled(feature_name: str):
    """Check if a specific feature is enabled"""
    features = get_polygon_setting('POLYGON_FEATURES', {})
    return features.get(feature_name, True)


def get_default_symbols(instrument_type: str):
    """Get default symbols for tracking"""
    symbols = get_polygon_setting('POLYGON_DEFAULT_SYMBOLS', {})
    return symbols.get(instrument_type.upper(), [])


def get_data_retention_days(data_type: str):
    """Get data retention period for specific data type"""
    retention = get_polygon_setting('POLYGON_DATA_RETENTION', {})
    retention_key = f"KEEP_{data_type.upper()}_DATA_DAYS"
    return retention.get(retention_key, 365)


def get_data_source_setting(setting_name: str):
    """Get data source configuration setting"""
    data_source = get_polygon_setting('POLYGON_DATA_SOURCE', {})
    return data_source.get(setting_name)


def get_websocket_setting(setting_name: str):
    """Get WebSocket configuration setting"""
    websocket_settings = get_polygon_setting('POLYGON_WEBSOCKET_SETTINGS', {})
    return websocket_settings.get(setting_name)


def should_use_websocket():
    """Determine if WebSocket should be used as primary data source"""
    primary_source = get_data_source_setting('PRIMARY_SOURCE')
    websocket_enabled = get_data_source_setting('ENABLE_WEBSOCKET')
    return primary_source == 'websocket' and websocket_enabled


def should_use_rest_api():
    """Determine if REST API should be used"""
    rest_enabled = get_data_source_setting('ENABLE_REST_API')
    return rest_enabled


def get_fallback_source():
    """Get fallback data source"""
    return get_data_source_setting('FALLBACK_SOURCE')


def is_websocket_enabled_for_market(market_type: str):
    """Check if WebSocket is enabled for specific market type"""
    setting_key = f"ENABLE_{market_type.upper()}_WS"
    return get_websocket_setting(setting_key)
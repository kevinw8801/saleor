from django.urls import path
from . import views

app_name = 'polygon'

urlpatterns = [
    # Blockchain endpoints
    path('webhook/', views.PolygonWebhookView.as_view(), name='webhook'),
    path('wallet/<str:wallet_address>/balance/', views.polygon_wallet_balance, name='wallet_balance'),
    
    # Stock endpoints
    path('api/stock/<str:symbol>/quote/', views.stock_quote, name='stock_quote'),
    path('api/stock/<str:symbol>/bars/', views.stock_bars, name='stock_bars'),
    path('api/stock/<str:symbol>/details/', views.stock_details, name='stock_details'),
    
    # Options endpoints
    path('api/options/<str:underlying_ticker>/chain/', views.options_chain, name='options_chain'),
    path('api/options/<str:option_ticker>/quote/', views.option_quote, name='option_quote'),
    
    # Crypto endpoints
    path('api/crypto/<str:symbol>/quote/', views.crypto_quote, name='crypto_quote'),
    path('api/crypto/<str:symbol>/bars/', views.crypto_bars, name='crypto_bars'),
    path('api/crypto/<str:symbol>/details/', views.crypto_details, name='crypto_details'),
    
    # Forex endpoints
    path('api/forex/<str:symbol>/quote/', views.forex_quote, name='forex_quote'),
    path('api/forex/<str:symbol>/bars/', views.forex_bars, name='forex_bars'),
    path('api/forex/<str:symbol>/details/', views.forex_details, name='forex_details'),
    
    # Market and search endpoints
    path('api/market/status/', views.market_status, name='market_status'),
    path('api/search/', views.search_tickers, name='search_tickers'),
    
    # Cache management
    path('api/cache/clear/', views.clear_cache, name='clear_cache'),
    path('api/cache/invalidate/', views.invalidate_cache, name='invalidate_cache'),
]
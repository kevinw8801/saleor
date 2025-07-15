from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
from datetime import datetime, date
import json

from .models import (
    PolygonTransaction, PolygonWallet, FinancialInstrument, 
    StockData, OptionData, CryptoData, ForexData
)
from .clients import PolygonIOClient
from .cache import CachedPolygonClient, PolygonCacheManager


@method_decorator(csrf_exempt, name='dispatch')
class PolygonWebhookView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            transaction_data = {
                'transaction_id': data.get('transaction_id'),
                'block_number': data.get('block_number'),
                'transaction_hash': data.get('transaction_hash'),
                'from_address': data.get('from_address'),
                'to_address': data.get('to_address'),
                'value': data.get('value'),
                'gas_used': data.get('gas_used'),
                'gas_price': data.get('gas_price'),
                'status': data.get('status', 'pending')
            }
            
            transaction, created = PolygonTransaction.objects.update_or_create(
                transaction_id=transaction_data['transaction_id'],
                defaults=transaction_data
            )
            
            return JsonResponse({
                'success': True,
                'transaction_id': transaction.transaction_id,
                'created': created
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


def _get_polygon_client():
    """Get cached Polygon.io client instance"""
    if not hasattr(_get_polygon_client, '_client'):
        try:
            api_key = getattr(settings, 'POLYGON_IO_API_KEY', None)
            if not api_key:
                raise ValueError("POLYGON_IO_API_KEY not configured in settings")
            
            polygon_client = PolygonIOClient(api_key)
            cache_manager = PolygonCacheManager()
            _get_polygon_client._client = CachedPolygonClient(polygon_client, cache_manager)
        except Exception as e:
            return None
    
    return _get_polygon_client._client


def _handle_api_error(e):
    """Handle API errors and return appropriate response"""
    return JsonResponse({
        'success': False,
        'error': str(e)
    }, status=500)


# Stock API endpoints
@require_http_methods(["GET"])
def stock_quote(request, symbol):
    """Get real-time stock quote"""
    try:
        client = _get_polygon_client()
        if not client:
            return JsonResponse({'error': 'Polygon.io client not configured'}, status=500)
        
        data = client.get_stock_quote(symbol.upper())
        return JsonResponse({
            'success': True,
            'symbol': symbol.upper(),
            'data': data
        })
    except Exception as e:
        return _handle_api_error(e)


@require_http_methods(["GET"])
def stock_bars(request, symbol):
    """Get stock price bars/aggregates"""
    try:
        client = _get_polygon_client()
        if not client:
            return JsonResponse({'error': 'Polygon.io client not configured'}, status=500)
        
        timespan = request.GET.get('timespan', 'day')
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        limit = int(request.GET.get('limit', 100))
        
        data = client.get_stock_bars(symbol.upper(), timespan, from_date, to_date, limit)
        return JsonResponse({
            'success': True,
            'symbol': symbol.upper(),
            'timespan': timespan,
            'data': data
        })
    except Exception as e:
        return _handle_api_error(e)


@require_http_methods(["GET"])
def stock_details(request, symbol):
    """Get stock ticker details"""
    try:
        client = _get_polygon_client()
        if not client:
            return JsonResponse({'error': 'Polygon.io client not configured'}, status=500)
        
        data = client.get_stock_details(symbol.upper())
        return JsonResponse({
            'success': True,
            'symbol': symbol.upper(),
            'data': data
        })
    except Exception as e:
        return _handle_api_error(e)


# Options API endpoints
@require_http_methods(["GET"])
def options_chain(request, underlying_ticker):
    """Get options chain for underlying asset"""
    try:
        client = _get_polygon_client()
        if not client:
            return JsonResponse({'error': 'Polygon.io client not configured'}, status=500)
        
        expiration_date = request.GET.get('expiration_date')
        option_type = request.GET.get('option_type')
        
        data = client.get_options_chain(underlying_ticker.upper(), expiration_date, option_type)
        return JsonResponse({
            'success': True,
            'underlying_ticker': underlying_ticker.upper(),
            'data': data
        })
    except Exception as e:
        return _handle_api_error(e)


@require_http_methods(["GET"])
def option_quote(request, option_ticker):
    """Get option quote"""
    try:
        client = _get_polygon_client()
        if not client:
            return JsonResponse({'error': 'Polygon.io client not configured'}, status=500)
        
        data = client.get_option_quote(option_ticker.upper())
        return JsonResponse({
            'success': True,
            'option_ticker': option_ticker.upper(),
            'data': data
        })
    except Exception as e:
        return _handle_api_error(e)


# Crypto API endpoints
@require_http_methods(["GET"])
def crypto_quote(request, symbol):
    """Get real-time crypto quote"""
    try:
        client = _get_polygon_client()
        if not client:
            return JsonResponse({'error': 'Polygon.io client not configured'}, status=500)
        
        data = client.get_crypto_quote(symbol.upper())
        return JsonResponse({
            'success': True,
            'symbol': symbol.upper(),
            'data': data
        })
    except Exception as e:
        return _handle_api_error(e)


@require_http_methods(["GET"])
def crypto_bars(request, symbol):
    """Get crypto price bars/aggregates"""
    try:
        client = _get_polygon_client()
        if not client:
            return JsonResponse({'error': 'Polygon.io client not configured'}, status=500)
        
        timespan = request.GET.get('timespan', 'hour')
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        limit = int(request.GET.get('limit', 100))
        
        data = client.get_crypto_bars(symbol.upper(), timespan, from_date, to_date, limit)
        return JsonResponse({
            'success': True,
            'symbol': symbol.upper(),
            'timespan': timespan,
            'data': data
        })
    except Exception as e:
        return _handle_api_error(e)


@require_http_methods(["GET"])
def crypto_details(request, symbol):
    """Get crypto ticker details"""
    try:
        client = _get_polygon_client()
        if not client:
            return JsonResponse({'error': 'Polygon.io client not configured'}, status=500)
        
        data = client.get_crypto_details(symbol.upper())
        return JsonResponse({
            'success': True,
            'symbol': symbol.upper(),
            'data': data
        })
    except Exception as e:
        return _handle_api_error(e)


# Forex API endpoints
@require_http_methods(["GET"])
def forex_quote(request, symbol):
    """Get real-time forex quote"""
    try:
        client = _get_polygon_client()
        if not client:
            return JsonResponse({'error': 'Polygon.io client not configured'}, status=500)
        
        data = client.get_forex_quote(symbol.upper())
        return JsonResponse({
            'success': True,
            'symbol': symbol.upper(),
            'data': data
        })
    except Exception as e:
        return _handle_api_error(e)


@require_http_methods(["GET"])
def forex_bars(request, symbol):
    """Get forex price bars/aggregates"""
    try:
        client = _get_polygon_client()
        if not client:
            return JsonResponse({'error': 'Polygon.io client not configured'}, status=500)
        
        timespan = request.GET.get('timespan', 'hour')
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        limit = int(request.GET.get('limit', 100))
        
        data = client.get_forex_bars(symbol.upper(), timespan, from_date, to_date, limit)
        return JsonResponse({
            'success': True,
            'symbol': symbol.upper(),
            'timespan': timespan,
            'data': data
        })
    except Exception as e:
        return _handle_api_error(e)


@require_http_methods(["GET"])
def forex_details(request, symbol):
    """Get forex ticker details"""
    try:
        client = _get_polygon_client()
        if not client:
            return JsonResponse({'error': 'Polygon.io client not configured'}, status=500)
        
        data = client.get_forex_details(symbol.upper())
        return JsonResponse({
            'success': True,
            'symbol': symbol.upper(),
            'data': data
        })
    except Exception as e:
        return _handle_api_error(e)


# Market status and search endpoints
@require_http_methods(["GET"])
def market_status(request):
    """Get current market status"""
    try:
        client = _get_polygon_client()
        if not client:
            return JsonResponse({'error': 'Polygon.io client not configured'}, status=500)
        
        data = client.get_market_status()
        return JsonResponse({
            'success': True,
            'data': data
        })
    except Exception as e:
        return _handle_api_error(e)


@require_http_methods(["GET"])
def search_tickers(request):
    """Search for tickers"""
    try:
        client = _get_polygon_client()
        if not client:
            return JsonResponse({'error': 'Polygon.io client not configured'}, status=500)
        
        search_query = request.GET.get('q', '').strip()
        if not search_query:
            return JsonResponse({'error': 'Search query parameter "q" is required'}, status=400)
        
        market = request.GET.get('market')
        
        data = client.search_tickers(search_query, market)
        return JsonResponse({
            'success': True,
            'query': search_query,
            'market': market,
            'data': data
        })
    except Exception as e:
        return _handle_api_error(e)


# Blockchain wallet endpoints (existing)
@require_http_methods(["GET"])
def polygon_wallet_balance(request, wallet_address):
    try:
        wallet = PolygonWallet.objects.get(wallet_address=wallet_address)
        return JsonResponse({
            'wallet_address': wallet.wallet_address,
            'balance': str(wallet.balance),
            'last_sync': wallet.last_sync.isoformat() if wallet.last_sync else None
        })
    except PolygonWallet.DoesNotExist:
        return JsonResponse({
            'error': 'Wallet not found'
        }, status=404)


# Cache management endpoints
@require_http_methods(["POST"])
@csrf_exempt
def clear_cache(request):
    """Clear expired cache entries"""
    try:
        cache_manager = PolygonCacheManager()
        cleared_count = cache_manager.clear_expired()
        return JsonResponse({
            'success': True,
            'cleared_entries': cleared_count
        })
    except Exception as e:
        return _handle_api_error(e)


@require_http_methods(["DELETE"])
@csrf_exempt
def invalidate_cache(request):
    """Invalidate specific cache key"""
    try:
        data = json.loads(request.body)
        cache_key = data.get('cache_key')
        
        if not cache_key:
            return JsonResponse({'error': 'cache_key is required'}, status=400)
        
        cache_manager = PolygonCacheManager()
        cache_manager.invalidate(cache_key)
        
        return JsonResponse({
            'success': True,
            'message': f'Cache key {cache_key} invalidated'
        })
    except Exception as e:
        return _handle_api_error(e)
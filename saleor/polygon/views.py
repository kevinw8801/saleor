from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
import json

from .models import PolygonTransaction, PolygonWallet


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
from django.contrib import admin
from .models import PolygonTransaction, PolygonContract, PolygonWallet


@admin.register(PolygonTransaction)
class PolygonTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'from_address', 'to_address', 'value', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('transaction_id', 'transaction_hash', 'from_address', 'to_address')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(PolygonContract)
class PolygonContractAdmin(admin.ModelAdmin):
    list_display = ('name', 'contract_address', 'contract_type', 'symbol', 'is_active', 'created_at')
    list_filter = ('contract_type', 'is_active', 'created_at')
    search_fields = ('name', 'contract_address', 'symbol')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('name',)


@admin.register(PolygonWallet)
class PolygonWalletAdmin(admin.ModelAdmin):
    list_display = ('wallet_address', 'label', 'balance', 'is_monitored', 'last_sync', 'created_at')
    list_filter = ('is_monitored', 'created_at', 'last_sync')
    search_fields = ('wallet_address', 'label')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('wallet_address',)
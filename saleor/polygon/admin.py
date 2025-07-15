from django.contrib import admin
from .models import (
    PolygonTransaction, PolygonContract, PolygonWallet,
    FinancialInstrument, StockData, OptionData, CryptoData, ForexData, MarketDataCache
)


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


@admin.register(FinancialInstrument)
class FinancialInstrumentAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'instrument_type', 'is_active', 'created_at')
    list_filter = ('instrument_type', 'is_active', 'created_at')
    search_fields = ('symbol', 'name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('symbol',)


@admin.register(StockData)
class StockDataAdmin(admin.ModelAdmin):
    list_display = ('instrument', 'timestamp', 'close_price', 'volume', 'created_at')
    list_filter = ('instrument__instrument_type', 'timestamp', 'created_at')
    search_fields = ('instrument__symbol', 'instrument__name')
    readonly_fields = ('created_at',)
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'


@admin.register(OptionData)
class OptionDataAdmin(admin.ModelAdmin):
    list_display = ('option_symbol', 'underlying_instrument', 'option_type', 'strike_price', 'expiration_date', 'last_price')
    list_filter = ('option_type', 'expiration_date', 'underlying_instrument', 'timestamp')
    search_fields = ('option_symbol', 'underlying_instrument__symbol')
    readonly_fields = ('created_at',)
    ordering = ('-timestamp',)
    date_hierarchy = 'expiration_date'


@admin.register(CryptoData)
class CryptoDataAdmin(admin.ModelAdmin):
    list_display = ('instrument', 'timestamp', 'close_price', 'volume', 'market_cap', 'created_at')
    list_filter = ('instrument', 'timestamp', 'created_at')
    search_fields = ('instrument__symbol', 'instrument__name')
    readonly_fields = ('created_at',)
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'


@admin.register(ForexData)
class ForexDataAdmin(admin.ModelAdmin):
    list_display = ('instrument', 'timestamp', 'close_rate', 'volume', 'created_at')
    list_filter = ('instrument', 'timestamp', 'created_at')
    search_fields = ('instrument__symbol', 'instrument__name')
    readonly_fields = ('created_at',)
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'


@admin.register(MarketDataCache)
class MarketDataCacheAdmin(admin.ModelAdmin):
    list_display = ('cache_key', 'expires_at', 'is_expired', 'created_at')
    list_filter = ('expires_at', 'created_at')
    search_fields = ('cache_key',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = 'Expired'
from django.db import models
from django.utils import timezone


class FinancialInstrument(models.Model):
    """Base model for all financial instruments"""
    
    INSTRUMENT_TYPES = (
        ('STOCK', 'Stock'),
        ('OPTION', 'Option'),
        ('CRYPTO', 'Cryptocurrency'),
        ('FOREX', 'Foreign Exchange'),
    )
    
    symbol = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    instrument_type = models.CharField(max_length=10, choices=INSTRUMENT_TYPES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'polygon_financial_instrument'
        ordering = ['symbol']
        indexes = [
            models.Index(fields=['symbol']),
            models.Index(fields=['instrument_type']),
        ]
    
    def __str__(self):
        return f"{self.symbol} - {self.name}"


class StockData(models.Model):
    """Model for stock market data"""
    
    instrument = models.ForeignKey(FinancialInstrument, on_delete=models.CASCADE, related_name='stock_data')
    timestamp = models.DateTimeField()
    open_price = models.DecimalField(max_digits=20, decimal_places=8)
    high_price = models.DecimalField(max_digits=20, decimal_places=8)
    low_price = models.DecimalField(max_digits=20, decimal_places=8)
    close_price = models.DecimalField(max_digits=20, decimal_places=8)
    volume = models.BigIntegerField()
    vwap = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    market_cap = models.DecimalField(max_digits=30, decimal_places=2, null=True, blank=True)
    pe_ratio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dividend_yield = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'polygon_stock_data'
        ordering = ['-timestamp']
        unique_together = ['instrument', 'timestamp']
        indexes = [
            models.Index(fields=['instrument', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.instrument.symbol} - {self.timestamp} - ${self.close_price}"


class OptionData(models.Model):
    """Model for options market data"""
    
    OPTION_TYPES = (
        ('CALL', 'Call Option'),
        ('PUT', 'Put Option'),
    )
    
    underlying_instrument = models.ForeignKey(FinancialInstrument, on_delete=models.CASCADE, related_name='options')
    option_symbol = models.CharField(max_length=50, unique=True)
    option_type = models.CharField(max_length=4, choices=OPTION_TYPES)
    strike_price = models.DecimalField(max_digits=20, decimal_places=8)
    expiration_date = models.DateField()
    timestamp = models.DateTimeField()
    bid_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    ask_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    last_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    volume = models.BigIntegerField(default=0)
    open_interest = models.BigIntegerField(default=0)
    implied_volatility = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    delta = models.DecimalField(max_digits=6, decimal_places=5, null=True, blank=True)
    gamma = models.DecimalField(max_digits=6, decimal_places=5, null=True, blank=True)
    theta = models.DecimalField(max_digits=6, decimal_places=5, null=True, blank=True)
    vega = models.DecimalField(max_digits=6, decimal_places=5, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'polygon_option_data'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['underlying_instrument', 'expiration_date']),
            models.Index(fields=['option_symbol']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.option_symbol} - {self.option_type} ${self.strike_price} exp {self.expiration_date}"


class CryptoData(models.Model):
    """Model for cryptocurrency market data"""
    
    instrument = models.ForeignKey(FinancialInstrument, on_delete=models.CASCADE, related_name='crypto_data')
    timestamp = models.DateTimeField()
    open_price = models.DecimalField(max_digits=20, decimal_places=8)
    high_price = models.DecimalField(max_digits=20, decimal_places=8)
    low_price = models.DecimalField(max_digits=20, decimal_places=8)
    close_price = models.DecimalField(max_digits=20, decimal_places=8)
    volume = models.DecimalField(max_digits=30, decimal_places=8)
    market_cap = models.DecimalField(max_digits=30, decimal_places=2, null=True, blank=True)
    circulating_supply = models.DecimalField(max_digits=30, decimal_places=8, null=True, blank=True)
    total_supply = models.DecimalField(max_digits=30, decimal_places=8, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'polygon_crypto_data'
        ordering = ['-timestamp']
        unique_together = ['instrument', 'timestamp']
        indexes = [
            models.Index(fields=['instrument', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.instrument.symbol} - {self.timestamp} - ${self.close_price}"


class ForexData(models.Model):
    """Model for foreign exchange market data"""
    
    instrument = models.ForeignKey(FinancialInstrument, on_delete=models.CASCADE, related_name='forex_data')
    timestamp = models.DateTimeField()
    open_rate = models.DecimalField(max_digits=20, decimal_places=8)
    high_rate = models.DecimalField(max_digits=20, decimal_places=8)
    low_rate = models.DecimalField(max_digits=20, decimal_places=8)
    close_rate = models.DecimalField(max_digits=20, decimal_places=8)
    volume = models.DecimalField(max_digits=30, decimal_places=8, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'polygon_forex_data'
        ordering = ['-timestamp']
        unique_together = ['instrument', 'timestamp']
        indexes = [
            models.Index(fields=['instrument', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.instrument.symbol} - {self.timestamp} - {self.close_rate}"


class MarketDataCache(models.Model):
    """Model for caching API responses"""
    
    cache_key = models.CharField(max_length=255, unique=True)
    data = models.JSONField()
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'polygon_market_data_cache'
        indexes = [
            models.Index(fields=['cache_key']),
            models.Index(fields=['expires_at']),
        ]
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f"Cache: {self.cache_key}"


class PolygonTransaction(models.Model):
    transaction_id = models.CharField(max_length=255, unique=True)
    block_number = models.BigIntegerField()
    transaction_hash = models.CharField(max_length=66)
    from_address = models.CharField(max_length=42)
    to_address = models.CharField(max_length=42)
    value = models.DecimalField(max_digits=36, decimal_places=18)
    gas_used = models.BigIntegerField()
    gas_price = models.DecimalField(max_digits=36, decimal_places=18)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'polygon_transaction'
        ordering = ['-created_at']

    def __str__(self):
        return f"Polygon Transaction {self.transaction_id}"


class PolygonContract(models.Model):
    CONTRACT_TYPES = (
        ('ERC20', 'ERC-20 Token'),
        ('ERC721', 'ERC-721 NFT'),
        ('ERC1155', 'ERC-1155 Multi Token'),
        ('CUSTOM', 'Custom Contract'),
    )

    contract_address = models.CharField(max_length=42, unique=True)
    contract_type = models.CharField(max_length=10, choices=CONTRACT_TYPES)
    name = models.CharField(max_length=255)
    symbol = models.CharField(max_length=50, blank=True)
    decimals = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'polygon_contract'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.contract_address})"


class PolygonWallet(models.Model):
    wallet_address = models.CharField(max_length=42, unique=True)
    label = models.CharField(max_length=255, blank=True)
    is_monitored = models.BooleanField(default=False)
    balance = models.DecimalField(max_digits=36, decimal_places=18, default=0)
    last_sync = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'polygon_wallet'
        ordering = ['wallet_address']

    def __str__(self):
        return f"Wallet {self.wallet_address}" + (f" ({self.label})" if self.label else "")
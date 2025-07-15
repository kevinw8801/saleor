from django.db import models


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
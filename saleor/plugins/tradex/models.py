from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models


class Operation(models.Model):
    """
    Model to store trading operations data.
    This represents individual trading operations with all relevant details.
    """
    
    # Timestamp for when the operation occurred
    date_time = models.DateTimeField(
        help_text="Date and time when the operation occurred"
    )
    
    # String field for operation type (buy, sell, dividend, etc.)
    operation = models.CharField(
        max_length=100,
        help_text="Type of operation (e.g., buy, sell, dividend, split)"
    )
    
    # Equity identifier (symbol or ISIN)
    equity_id = models.CharField(
        max_length=50,
        help_text="Equity identifier (ticker symbol, ISIN, etc.)"
    )
    
    # Human-readable equity name
    equity_name = models.CharField(
        max_length=255,
        help_text="Human-readable name of the equity"
    )
    
    # Market where the operation took place
    market = models.CharField(
        max_length=100,
        help_text="Market or exchange where the operation took place"
    )
    
    # Amount/quantity - non-negative numeric value
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Amount or quantity of the operation (non-negative)"
    )
    
    # Fee charged for the operation - non-negative numeric value
    fee = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Fee charged for the operation (non-negative)"
    )
    
    # Currency code (ISO 4217)
    currency = models.CharField(
        max_length=3,
        help_text="Currency code (ISO 4217 format, e.g., USD, EUR)"
    )
    
    # Price per unit - non-negative numeric value
    price = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Price per unit (non-negative)"
    )
    
    # Status of the operation
    status = models.CharField(
        max_length=50,
        help_text="Status of the operation (e.g., completed, pending, failed)"
    )
    
    # Metadata fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tradex_operation'
        ordering = ['-date_time', '-created_at']
        indexes = [
            models.Index(fields=['equity_id']),
            models.Index(fields=['date_time']),
            models.Index(fields=['operation']),
            models.Index(fields=['status']),
            models.Index(fields=['market']),
        ]
        verbose_name = 'Trading Operation'
        verbose_name_plural = 'Trading Operations'
    
    def __str__(self):
        return f"{self.operation} {self.amount} {self.equity_id} @ {self.price} {self.currency}"
    
    @property
    def total_value(self):
        """Calculate total value including fees."""
        return (self.amount * self.price) + self.fee
    
    @property
    def net_value(self):
        """Calculate net value excluding fees."""
        return self.amount * self.price
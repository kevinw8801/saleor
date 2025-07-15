import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator

from ...warehouse.models import Stock
from .constants import SECURITIES_MOVEMENT_TYPES, NOTIFICATION_TYPES


class Securities(models.Model):
    """Master table for securities data (stocks, ETFs, bonds, etc.)"""
    
    SECURITY_TYPES = [
        ('STOCK', 'Stock'),
        ('ETF', 'ETF'),
        ('MUTUAL_FUND', 'Mutual Fund'),
        ('BOND', 'Bond'),
        ('OPTION', 'Option'),
        ('FUTURE', 'Future'),
        ('CRYPTO', 'Cryptocurrency'),
        ('FOREX', 'Forex'),
        ('COMMODITY', 'Commodity'),
        ('INDEX', 'Index'),
    ]
    
    security_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the security"
    )
    symbol = models.CharField(
        max_length=16,
        help_text="Trading symbol for the security"
    )
    security_type = models.CharField(
        max_length=12,
        choices=SECURITY_TYPES,
        help_text="Type of security (stock, ETF, etc.)"
    )
    name = models.CharField(
        max_length=255,
        help_text="Full name of the security"
    )
    exchange = models.CharField(
        max_length=10,
        blank=True,
        help_text="Exchange where the security is traded"
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Currency of the security"
    )
    sector = models.CharField(
        max_length=50,
        blank=True,
        help_text="Business sector"
    )
    industry = models.CharField(
        max_length=50,
        blank=True,
        help_text="Industry classification"
    )
    country = models.CharField(
        max_length=3,
        blank=True,
        help_text="Country code (ISO 3166-1 alpha-3)"
    )
    market_cap = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Market capitalization in base currency"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of the security"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the security is actively traded"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the security record was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When the security record was last updated"
    )
    
    class Meta:
        db_table = 'securities'
        verbose_name = 'Security'
        verbose_name_plural = 'Securities'
        unique_together = ['symbol', 'security_type']
        indexes = [
            models.Index(fields=['symbol']),
            models.Index(fields=['security_type']),
            models.Index(fields=['exchange']),
            models.Index(fields=['sector']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['symbol']
    
    def __str__(self):
        return f"{self.symbol} ({self.security_type}) - {self.name}"
    
    @property
    def display_name(self):
        """Display name combining symbol and name"""
        return f"{self.symbol} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Ensure symbol is uppercase
        self.symbol = self.symbol.upper()
        super().save(*args, **kwargs)


class SecuritiesMovement(models.Model):
    """Track all securities movements and changes"""
    
    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name='securities_movements'
    )
    quantity_change = models.IntegerField(
        help_text="Positive for increase, negative for decrease"
    )
    previous_quantity = models.IntegerField()
    new_quantity = models.IntegerField()
    movement_type = models.CharField(
        max_length=20,
        choices=[(t, t.title()) for t in SECURITIES_MOVEMENT_TYPES],
        default='adjustment'
    )
    timestamp = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)
    reference_order = models.CharField(max_length=100, blank=True)
    created_by = models.CharField(max_length=255, blank=True)
    
    class Meta:
        db_table = 'securities_movement'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['stock', 'timestamp']),
            models.Index(fields=['movement_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"Securities {self.stock.id}: {self.quantity_change:+d} ({self.movement_type})"


class SecuritiesAlert(models.Model):
    """Store securities alerts and notifications"""
    
    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name='securities_alerts'
    )
    alert_type = models.CharField(
        max_length=20,
        choices=[(t, t.replace('_', ' ').title()) for t in NOTIFICATION_TYPES]
    )
    message = models.TextField()
    quantity_at_alert = models.IntegerField()
    threshold = models.IntegerField(null=True, blank=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'securities_alert'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stock', 'alert_type']),
            models.Index(fields=['is_resolved', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.alert_type} alert for {self.stock}"
    
    def resolve(self):
        """Mark alert as resolved"""
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.save()


class SecuritiesSettings(models.Model):
    """Per-securities configuration settings"""
    
    stock = models.OneToOneField(
        Stock,
        on_delete=models.CASCADE,
        related_name='securities_settings'
    )
    reorder_point = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Quantity threshold to trigger reorder"
    )
    reorder_quantity = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Quantity to order when reorder point is reached"
    )
    safety_stock = models.IntegerField(
        validators=[MinValueValidator(0)],
        default=0,
        help_text="Safety securities buffer quantity"
    )
    max_stock_level = models.IntegerField(
        validators=[MinValueValidator(1)],
        null=True,
        blank=True,
        help_text="Maximum securities level before overstock alert"
    )
    lead_time_days = models.IntegerField(
        validators=[MinValueValidator(0)],
        default=7,
        help_text="Lead time for restocking in days"
    )
    enable_auto_reorder = models.BooleanField(
        default=False,
        help_text="Enable automatic reorder suggestions"
    )
    track_expiry = models.BooleanField(
        default=False,
        help_text="Track expiry dates for this securities"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'securities_settings'
    
    def __str__(self):
        return f"Settings for {self.stock}"


class SecuritiesForecast(models.Model):
    """Store securities demand forecasting data"""
    
    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name='securities_forecasts'
    )
    forecast_date = models.DateField()
    predicted_demand = models.IntegerField(
        validators=[MinValueValidator(0)]
    )
    confidence_level = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Confidence level as percentage (0-100)"
    )
    actual_demand = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    forecast_method = models.CharField(
        max_length=50,
        default='moving_average'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'securities_forecast'
        unique_together = ['stock', 'forecast_date', 'forecast_method']
        ordering = ['-forecast_date']
        indexes = [
            models.Index(fields=['stock', 'forecast_date']),
            models.Index(fields=['forecast_date']),
        ]
    
    def __str__(self):
        return f"Forecast for {self.stock} on {self.forecast_date}"
    
    @property
    def accuracy(self):
        """Calculate forecast accuracy if actual demand is available"""
        if self.actual_demand is None:
            return None
        
        if self.predicted_demand == 0 and self.actual_demand == 0:
            return 100.0
        
        if self.predicted_demand == 0:
            return 0.0
        
        error = abs(self.predicted_demand - self.actual_demand)
        accuracy = max(0, 100 - (error / self.predicted_demand * 100))
        return round(accuracy, 2)


class SecuritiesBatch(models.Model):
    """Track securities batches with expiry dates and batch numbers"""
    
    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name='securities_batches'
    )
    batch_number = models.CharField(max_length=100)
    quantity = models.IntegerField(validators=[MinValueValidator(0)])
    cost_per_unit = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True
    )
    expiry_date = models.DateField(null=True, blank=True)
    received_date = models.DateField(auto_now_add=True)
    supplier_reference = models.CharField(max_length=255, blank=True)
    is_expired = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'securities_batch'
        unique_together = ['stock', 'batch_number']
        ordering = ['expiry_date', 'received_date']
        indexes = [
            models.Index(fields=['stock', 'expiry_date']),
            models.Index(fields=['expiry_date', 'is_expired']),
        ]
    
    def __str__(self):
        return f"Batch {self.batch_number} for {self.stock}"
    
    def is_expiring_soon(self, days=7):
        """Check if batch is expiring within specified days"""
        if not self.expiry_date:
            return False
        
        days_until_expiry = (self.expiry_date - timezone.now().date()).days
        return days_until_expiry <= days
    
    def mark_expired(self):
        """Mark batch as expired"""
        self.is_expired = True
        self.save()


class ReorderSuggestion(models.Model):
    """Store automatic reorder suggestions"""
    
    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name='securities_reorder_suggestions'
    )
    suggested_quantity = models.IntegerField(validators=[MinValueValidator(1)])
    reason = models.TextField()
    urgency_level = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ],
        default='medium'
    )
    estimated_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    is_approved = models.BooleanField(default=False)
    is_processed = models.BooleanField(default=False)
    approved_by = models.CharField(max_length=255, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'securities_reorder_suggestion'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stock', 'is_processed']),
            models.Index(fields=['urgency_level', 'created_at']),
        ]
    
    def __str__(self):
        return f"Reorder {self.suggested_quantity} units for {self.stock}"
    
    def approve(self, approved_by=None):
        """Approve reorder suggestion"""
        self.is_approved = True
        if approved_by:
            self.approved_by = approved_by
        self.save()
    
    def process(self):
        """Mark suggestion as processed"""
        self.is_processed = True
        self.processed_at = timezone.now()
        self.save()
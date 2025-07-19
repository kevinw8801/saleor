from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models
from django.conf import settings


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


class Holding(models.Model):
    """
    Model to store portfolio holdings data.
    This represents individual holdings within a portfolio.
    """
    
    # Unique identifier for the holding
    id = models.CharField(
        max_length=100,
        primary_key=True,
        help_text="Unique identifier for the holding"
    )
    
    # Amount/quantity - non-negative integer
    amount = models.PositiveIntegerField(
        help_text="Amount or quantity of the holding (non-negative integer)"
    )
    
    # Purchase price - non-negative numeric value
    purchase_price = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Purchase price per unit (non-negative)"
    )
    
    # Purchase timestamp
    purchase_time = models.DateTimeField(
        help_text="Date and time when the holding was purchased"
    )
    
    # Market where the holding was purchased
    market = models.CharField(
        max_length=100,
        help_text="Market or exchange where the holding was purchased"
    )
    
    # Currency code (ISO 4217)
    currency = models.CharField(
        max_length=3,
        help_text="Currency code (ISO 4217 format, e.g., USD, EUR)"
    )
    
    # Metadata fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tradex_holding'
        ordering = ['-purchase_time', '-created_at']
        indexes = [
            models.Index(fields=['purchase_time']),
            models.Index(fields=['market']),
            models.Index(fields=['amount']),
            models.Index(fields=['currency']),
        ]
        verbose_name = 'Portfolio Holding'
        verbose_name_plural = 'Portfolio Holdings'
    
    def __str__(self):
        return f"Holding {self.id}: {self.amount} @ {self.purchase_price} {self.currency} ({self.market})"
    
    @property
    def total_value(self):
        """Calculate total value of the holding."""
        return self.amount * self.purchase_price


class ProductUserAssociation(models.Model):
    """
    Model to track user associations with products in the Tradex plugin.
    Stores information about who created/modified products and when.
    """
    
    ACTION_TYPES = [
        ('created', 'Product Created'),
        ('updated', 'Product Updated'),
        ('deleted', 'Product Deleted'),
        ('variant_created', 'Product Variant Created'),
        ('variant_updated', 'Product Variant Updated'),
        ('variant_deleted', 'Product Variant Deleted'),
        ('media_created', 'Product Media Created'),
        ('media_updated', 'Product Media Updated'),
        ('media_deleted', 'Product Media Deleted'),
    ]
    
    # Foreign key to Saleor's Product model
    product = models.ForeignKey(
        'product.Product',
        on_delete=models.CASCADE,
        related_name='tradex_user_associations',
        help_text="Reference to the Saleor product"
    )
    
    # Foreign key to User model - nullable for system actions
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tradex_product_associations',
        help_text="User who performed the action (null for system actions)"
    )
    
    # Action type performed
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_TYPES,
        default='created',
        help_text="Type of action performed on the product"
    )
    
    # Timestamp of the action
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When the action was performed"
    )
    
    # Additional context data (JSON field for flexibility)
    context_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional context about the action (e.g., variant ID, changes made)"
    )
    
    # User agent or source of the action
    source = models.CharField(
        max_length=100,
        blank=True,
        help_text="Source of the action (e.g., 'graphql_api', 'admin_panel', 'plugin')"
    )
    
    # IP address for audit trail
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the user who performed the action"
    )
    
    class Meta:
        db_table = 'tradex_product_user_association'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['product', 'action_type']),
            models.Index(fields=['user', 'action_type']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['action_type', 'timestamp']),
        ]
        verbose_name = 'Product User Association'
        verbose_name_plural = 'Product User Associations'
    
    def __str__(self):
        user_str = f"User {self.user.username}" if self.user else "System"
        return f"{user_str} {self.action_type} product {self.product.name} at {self.timestamp}"
    
    @classmethod
    def track_action(cls, product, user, action_type, context_data=None, source=None, ip_address=None):
        """
        Convenience method to track a user action on a product.
        
        Args:
            product: Product instance
            user: User instance (can be None for system actions)
            action_type: Type of action performed
            context_data: Additional context data (dict)
            source: Source of the action
            ip_address: IP address of the user
        
        Returns:
            ProductUserAssociation instance
        """
        return cls.objects.create(
            product=product,
            user=user,
            action_type=action_type,
            context_data=context_data or {},
            source=source or 'unknown',
            ip_address=ip_address
        )
    
    @classmethod
    def get_product_creator(cls, product):
        """
        Get the user who created the product.
        
        Args:
            product: Product instance
            
        Returns:
            User instance or None
        """
        association = cls.objects.filter(
            product=product,
            action_type='created'
        ).first()
        return association.user if association else None
    
    @classmethod
    def get_user_products(cls, user, action_type=None):
        """
        Get all products associated with a user.
        
        Args:
            user: User instance
            action_type: Optional filter by action type
            
        Returns:
            QuerySet of Product instances
        """
        queryset = cls.objects.filter(user=user)
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        
        return queryset.values_list('product', flat=True).distinct()
    
    @classmethod
    def get_product_history(cls, product):
        """
        Get the complete action history for a product.
        
        Args:
            product: Product instance
            
        Returns:
            QuerySet of ProductUserAssociation instances
        """
        return cls.objects.filter(product=product).order_by('-timestamp')
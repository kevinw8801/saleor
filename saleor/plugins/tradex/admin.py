from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Operation, Holding, ProductUserAssociation


@admin.register(Operation)
class OperationAdmin(admin.ModelAdmin):
    """
    Admin interface for trading operations.
    """
    list_display = [
        'date_time',
        'operation',
        'equity_id',
        'equity_name',
        'amount',
        'price',
        'currency',
        'status',
        'total_value'
    ]
    
    list_filter = [
        'operation',
        'status',
        'market',
        'currency',
        'date_time'
    ]
    
    search_fields = [
        'equity_id',
        'equity_name',
        'market'
    ]
    
    readonly_fields = [
        'total_value',
        'net_value',
        'created_at',
        'updated_at'
    ]
    
    date_hierarchy = 'date_time'
    
    ordering = ['-date_time', '-created_at']
    
    fieldsets = (
        ('Operation Details', {
            'fields': ('date_time', 'operation', 'status')
        }),
        ('Equity Information', {
            'fields': ('equity_id', 'equity_name', 'market')
        }),
        ('Financial Details', {
            'fields': ('amount', 'price', 'fee', 'currency')
        }),
        ('Calculated Values', {
            'fields': ('total_value', 'net_value'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_value(self, obj):
        """Display total value in admin."""
        return f"{obj.total_value:.4f} {obj.currency}"
    total_value.short_description = 'Total Value'


@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    """
    Admin interface for portfolio holdings.
    """
    list_display = [
        'id',
        'amount',
        'purchase_price',
        'purchase_time',
        'market',
        'currency',
        'total_value'
    ]
    
    list_filter = [
        'market',
        'currency',
        'purchase_time'
    ]
    
    search_fields = [
        'id',
        'market'
    ]
    
    readonly_fields = [
        'total_value',
        'created_at',
        'updated_at'
    ]
    
    date_hierarchy = 'purchase_time'
    ordering = ['-purchase_time', '-created_at']
    
    def total_value(self, obj):
        """Display total value in admin."""
        return f"{obj.total_value:.4f} {obj.currency}"
    total_value.short_description = 'Total Value'


@admin.register(ProductUserAssociation)
class ProductUserAssociationAdmin(admin.ModelAdmin):
    """
    Admin interface for product user associations.
    """
    list_display = [
        'product_link',
        'user_link',
        'action_type',
        'timestamp',
        'source',
        'ip_address'
    ]
    
    list_filter = [
        'action_type',
        'source',
        'timestamp',
        ('user', admin.RelatedFieldListFilter),
    ]
    
    search_fields = [
        'product__name',
        'product__slug',
        'user__username',
        'user__email',
        'ip_address'
    ]
    
    readonly_fields = [
        'product',
        'user',
        'action_type',
        'timestamp',
        'context_data',
        'source',
        'ip_address',
        'formatted_context_data'
    ]
    
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('product', 'user', 'action_type', 'timestamp')
        }),
        ('Action Context', {
            'fields': ('source', 'ip_address', 'formatted_context_data'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Disable manual addition of associations."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Make associations read-only."""
        return False
    
    def product_link(self, obj):
        """Create a link to the product in admin."""
        if obj.product:
            url = reverse('admin:product_product_change', args=[obj.product.pk])
            return format_html('<a href="{}">{}</a>', url, obj.product.name[:50])
        return '-'
    product_link.short_description = 'Product'
    product_link.admin_order_field = 'product__name'
    
    def user_link(self, obj):
        """Create a link to the user in admin."""
        if obj.user:
            url = reverse('admin:account_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return 'System'
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__username'
    
    def formatted_context_data(self, obj):
        """Display context data in a readable format."""
        if not obj.context_data:
            return '-'
        
        html_parts = []
        for key, value in obj.context_data.items():
            html_parts.append(f'<strong>{key}:</strong> {value}')
        
        return format_html('<br>'.join(html_parts))
    formatted_context_data.short_description = 'Context Data'
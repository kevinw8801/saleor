from django.contrib import admin
from .models import Operation


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
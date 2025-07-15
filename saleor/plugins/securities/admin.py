from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils import timezone

from .models import (
    Securities,
    SecurityDailyPrices,
    SecuritiesMovement,
    SecuritiesAlert,
    SecuritiesSettings,
    SecuritiesForecast,
    SecuritiesBatch,
    ReorderSuggestion
)


@admin.register(Securities)
class SecuritiesAdmin(admin.ModelAdmin):
    list_display = (
        'symbol',
        'security_type',
        'name',
        'exchange',
        'currency',
        'sector',
        'industry',
        'is_active',
        'created_at'
    )
    list_filter = (
        'security_type',
        'exchange',
        'currency',
        'sector',
        'industry',
        'is_active',
        'created_at'
    )
    search_fields = (
        'symbol',
        'name',
        'description',
        'sector',
        'industry'
    )
    readonly_fields = (
        'security_id',
        'created_at',
        'updated_at'
    )
    ordering = ('symbol',)
    list_per_page = 50
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'security_id',
                'symbol',
                'security_type',
                'name',
                'description'
            )
        }),
        ('Trading Information', {
            'fields': (
                'exchange',
                'currency',
                'is_active'
            )
        }),
        ('Classification', {
            'fields': (
                'sector',
                'industry',
                'country'
            )
        }),
        ('Financial Data', {
            'fields': (
                'market_cap',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(SecurityDailyPrices)
class SecurityDailyPricesAdmin(admin.ModelAdmin):
    list_display = (
        'security_symbol',
        'date',
        'close_price',
        'open_price',
        'high_price',
        'low_price',
        'volume',
        'price_change_display',
        'price_change_percent_display'
    )
    list_filter = (
        'date',
        'security__security_type',
        'security__exchange',
        'security__currency'
    )
    search_fields = (
        'security__symbol',
        'security__name'
    )
    readonly_fields = (
        'created_at',
        'updated_at',
        'price_change',
        'price_change_percent',
        'trading_range'
    )
    ordering = ('-date', 'security__symbol')
    list_per_page = 100
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Security & Date', {
            'fields': (
                'security',
                'date'
            )
        }),
        ('Price Data', {
            'fields': (
                'open_price',
                'high_price',
                'low_price',
                'close_price',
                'adjusted_close'
            )
        }),
        ('Volume', {
            'fields': (
                'volume',
            )
        }),
        ('Calculated Fields', {
            'fields': (
                'price_change',
                'price_change_percent',
                'trading_range'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def security_symbol(self, obj):
        return obj.security.symbol
    security_symbol.short_description = 'Symbol'
    security_symbol.admin_order_field = 'security__symbol'
    
    def price_change_display(self, obj):
        change = obj.price_change
        color = "green" if change > 0 else "red" if change < 0 else "black"
        return format_html(
            '<span style="color: {};">{:+.4f}</span>',
            color,
            change
        )
    price_change_display.short_description = 'Change'
    
    def price_change_percent_display(self, obj):
        percent = obj.price_change_percent
        color = "green" if percent > 0 else "red" if percent < 0 else "black"
        return format_html(
            '<span style="color: {};">{:+.2f}%</span>',
            color,
            percent
        )
    price_change_percent_display.short_description = 'Change %'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('security')


@admin.register(SecuritiesMovement)
class SecuritiesMovementAdmin(admin.ModelAdmin):
    list_display = (
        'stock_link',
        'movement_type',
        'quantity_change',
        'previous_quantity',
        'new_quantity',
        'timestamp',
        'created_by'
    )
    list_filter = (
        'movement_type',
        'timestamp',
        'stock__warehouse'
    )
    search_fields = (
        'stock__product_variant__sku',
        'stock__product_variant__product__name',
        'reference_order',
        'notes'
    )
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    
    def stock_link(self, obj):
        url = reverse('admin:warehouse_stock_change', args=[obj.stock.id])
        return format_html('<a href="{}">{}</a>', url, obj.stock)
    stock_link.short_description = 'Stock'


@admin.register(SecuritiesAlert)
class SecuritiesAlertAdmin(admin.ModelAdmin):
    list_display = (
        'stock_link',
        'alert_type',
        'quantity_at_alert',
        'threshold',
        'is_resolved',
        'created_at'
    )
    list_filter = (
        'alert_type',
        'is_resolved',
        'created_at',
        'stock__warehouse'
    )
    search_fields = (
        'stock__product_variant__sku',
        'stock__product_variant__product__name',
        'message'
    )
    readonly_fields = ('created_at', 'resolved_at')
    actions = ['mark_resolved']
    
    def stock_link(self, obj):
        url = reverse('admin:warehouse_stock_change', args=[obj.stock.id])
        return format_html('<a href="{}">{}</a>', url, obj.stock)
    stock_link.short_description = 'Stock'
    
    def mark_resolved(self, request, queryset):
        updated = queryset.filter(is_resolved=False).update(
            is_resolved=True,
            resolved_at=timezone.now()
        )
        self.message_user(request, f'{updated} alerts marked as resolved.')
    mark_resolved.short_description = 'Mark selected alerts as resolved'


@admin.register(SecuritiesSettings)
class SecuritiesSettingsAdmin(admin.ModelAdmin):
    list_display = (
        'stock_link',
        'reorder_point',
        'reorder_quantity',
        'safety_stock',
        'max_stock_level',
        'lead_time_days',
        'enable_auto_reorder',
        'track_expiry'
    )
    list_filter = (
        'enable_auto_reorder',
        'track_expiry',
        'stock__warehouse'
    )
    search_fields = (
        'stock__product_variant__sku',
        'stock__product_variant__product__name'
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def stock_link(self, obj):
        url = reverse('admin:warehouse_stock_change', args=[obj.stock.id])
        return format_html('<a href="{}">{}</a>', url, obj.stock)
    stock_link.short_description = 'Stock'


@admin.register(SecuritiesForecast)
class SecuritiesForecastAdmin(admin.ModelAdmin):
    list_display = (
        'stock_link',
        'forecast_date',
        'predicted_demand',
        'actual_demand',
        'accuracy_display',
        'confidence_level',
        'forecast_method'
    )
    list_filter = (
        'forecast_date',
        'forecast_method',
        'stock__warehouse'
    )
    search_fields = (
        'stock__product_variant__sku',
        'stock__product_variant__product__name'
    )
    readonly_fields = ('created_at', 'accuracy_display')
    date_hierarchy = 'forecast_date'
    
    def stock_link(self, obj):
        url = reverse('admin:warehouse_stock_change', args=[obj.stock.id])
        return format_html('<a href="{}">{}</a>', url, obj.stock)
    stock_link.short_description = 'Stock'
    
    def accuracy_display(self, obj):
        accuracy = obj.accuracy
        if accuracy is None:
            return "N/A"
        
        color = "green" if accuracy >= 80 else "orange" if accuracy >= 60 else "red"
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color,
            accuracy
        )
    accuracy_display.short_description = 'Accuracy'


@admin.register(SecuritiesBatch)
class SecuritiesBatchAdmin(admin.ModelAdmin):
    list_display = (
        'stock_link',
        'batch_number',
        'quantity',
        'cost_per_unit',
        'expiry_date',
        'expiry_status',
        'received_date',
        'supplier_reference'
    )
    list_filter = (
        'is_expired',
        'expiry_date',
        'received_date',
        'stock__warehouse'
    )
    search_fields = (
        'batch_number',
        'stock__product_variant__sku',
        'stock__product_variant__product__name',
        'supplier_reference'
    )
    readonly_fields = ('received_date',)
    date_hierarchy = 'expiry_date'
    actions = ['mark_expired']
    
    def stock_link(self, obj):
        url = reverse('admin:warehouse_stock_change', args=[obj.stock.id])
        return format_html('<a href="{}">{}</a>', url, obj.stock)
    stock_link.short_description = 'Stock'
    
    def expiry_status(self, obj):
        if obj.is_expired:
            return format_html('<span style="color: red;">Expired</span>')
        elif obj.is_expiring_soon(7):
            return format_html('<span style="color: orange;">Expiring Soon</span>')
        elif obj.expiry_date:
            return format_html('<span style="color: green;">Good</span>')
        else:
            return "No Expiry"
    expiry_status.short_description = 'Status'
    
    def mark_expired(self, request, queryset):
        updated = queryset.filter(is_expired=False).update(is_expired=True)
        self.message_user(request, f'{updated} batches marked as expired.')
    mark_expired.short_description = 'Mark selected batches as expired'


@admin.register(ReorderSuggestion)
class ReorderSuggestionAdmin(admin.ModelAdmin):
    list_display = (
        'stock_link',
        'suggested_quantity',
        'urgency_level',
        'estimated_cost',
        'is_approved',
        'is_processed',
        'created_at'
    )
    list_filter = (
        'urgency_level',
        'is_approved',
        'is_processed',
        'created_at',
        'stock__warehouse'
    )
    search_fields = (
        'stock__product_variant__sku',
        'stock__product_variant__product__name',
        'reason',
        'approved_by'
    )
    readonly_fields = ('created_at', 'processed_at')
    actions = ['approve_suggestions', 'mark_processed']
    
    def stock_link(self, obj):
        url = reverse('admin:warehouse_stock_change', args=[obj.stock.id])
        return format_html('<a href="{}">{}</a>', url, obj.stock)
    stock_link.short_description = 'Stock'
    
    def approve_suggestions(self, request, queryset):
        updated = queryset.filter(is_approved=False).update(
            is_approved=True,
            approved_by=request.user.username if request.user else 'admin'
        )
        self.message_user(request, f'{updated} suggestions approved.')
    approve_suggestions.short_description = 'Approve selected suggestions'
    
    def mark_processed(self, request, queryset):
        updated = queryset.filter(is_processed=False).update(
            is_processed=True,
            processed_at=timezone.now()
        )
        self.message_user(request, f'{updated} suggestions marked as processed.')
    mark_processed.short_description = 'Mark selected suggestions as processed'
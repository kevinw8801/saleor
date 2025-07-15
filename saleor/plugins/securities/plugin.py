from typing import TYPE_CHECKING, Any, Dict, List, Optional
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

from ..base_plugin import BasePlugin, ConfigurationTypeField
from .constants import PLUGIN_ID, DEFAULT_SECURITIES_BUFFER, DEFAULT_REORDER_POINT, DEFAULT_REORDER_QUANTITY
from .utils import (
    calculate_securities_level,
    check_low_securities_threshold,
    generate_securities_report,
    predict_securities_needs,
    create_security,
    get_security_by_symbol,
    search_securities,
    get_securities_by_type,
    update_security_market_data,
    get_securities_statistics,
    add_daily_price,
    get_latest_price,
    get_price_history,
    get_price_by_date,
    bulk_add_daily_prices,
    get_price_statistics,
)

if TYPE_CHECKING:
    from ...product.models import ProductVariant
    from ...warehouse.models import Stock


class SecuritiesPlugin(BasePlugin):
    PLUGIN_ID = PLUGIN_ID
    PLUGIN_NAME = "Securities Management"
    PLUGIN_DESCRIPTION = "Advanced securities management and inventory optimization plugin for Saleor"
    DEFAULT_ACTIVE = True
    CONFIGURATION_PER_CHANNEL = False
    
    DEFAULT_CONFIGURATION = [
        {"name": "enable_securities_notifications", "value": True},
        {"name": "enable_automatic_reordering", "value": False},
        {"name": "default_securities_buffer", "value": DEFAULT_SECURITIES_BUFFER},
        {"name": "default_reorder_point", "value": DEFAULT_REORDER_POINT},
        {"name": "default_reorder_quantity", "value": DEFAULT_REORDER_QUANTITY},
        {"name": "low_securities_threshold_percentage", "value": 20},
        {"name": "critical_securities_threshold_percentage", "value": 5},
        {"name": "enable_securities_forecasting", "value": True},
        {"name": "forecast_days", "value": 30},
        {"name": "enable_expired_securities_tracking", "value": True},
        {"name": "notification_email", "value": None},
        {"name": "webhook_url", "value": None},
    ]

    CONFIG_STRUCTURE = {
        "enable_securities_notifications": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Enable automatic securities level notifications",
            "label": "Enable Securities Notifications",
        },
        "enable_automatic_reordering": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Enable automatic reorder suggestions",
            "label": "Enable Automatic Reordering",
        },
        "default_securities_buffer": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Default safety securities buffer quantity",
            "label": "Default Securities Buffer",
        },
        "default_reorder_point": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Default reorder point threshold",
            "label": "Default Reorder Point",
        },
        "default_reorder_quantity": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Default quantity to reorder",
            "label": "Default Reorder Quantity",
        },
        "low_securities_threshold_percentage": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Percentage threshold for low securities warnings",
            "label": "Low Securities Threshold (%)",
        },
        "critical_securities_threshold_percentage": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Percentage threshold for critical securities warnings",
            "label": "Critical Securities Threshold (%)",
        },
        "enable_securities_forecasting": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Enable securities demand forecasting",
            "label": "Enable Securities Forecasting",
        },
        "forecast_days": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Number of days to forecast securities needs",
            "label": "Forecast Days",
        },
        "enable_expired_securities_tracking": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Track and alert for expired securities",
            "label": "Enable Expired Securities Tracking",
        },
        "notification_email": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Email address for securities notifications",
            "label": "Notification Email",
        },
        "webhook_url": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Webhook URL for securities notifications",
            "label": "Webhook URL",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def product_variant_stock_updated(
        self,
        stock: "Stock",
        previous_value: int,
        **kwargs
    ) -> None:
        """Handle stock update events for monitoring and notifications"""
        if not self.active:
            return

        try:
            # Check securities levels and trigger notifications if needed
            self._check_securities_levels(stock)
            
            # Log securities movement
            self._log_securities_movement(stock, previous_value)
            
            # Check for automatic reordering
            if self._get_config_value("enable_automatic_reordering"):
                self._check_reorder_point(stock)
                
        except Exception as e:
            # Log error but don't break the flow
            pass

    def order_created(self, order, previous_value, **kwargs) -> None:
        """Handle order creation to update securities forecasting"""
        if not self.active:
            return

        try:
            # Update securities forecasting data based on new order
            if self._get_config_value("enable_securities_forecasting"):
                self._update_demand_forecast(order)
        except Exception:
            pass

    def _check_securities_levels(self, stock: "Stock") -> None:
        """Check securities levels and send notifications if needed"""
        if not self._get_config_value("enable_securities_notifications"):
            return

        low_threshold = int(self._get_config_value("low_securities_threshold_percentage", 20))
        critical_threshold = int(self._get_config_value("critical_securities_threshold_percentage", 5))
        
        securities_level = calculate_securities_level(stock, low_threshold, critical_threshold)
        
        if securities_level in ["low", "critical"]:
            self._send_securities_notification(stock, securities_level)

    def _log_securities_movement(self, stock: "Stock", previous_value: int) -> None:
        """Log securities movement for tracking purposes"""
        try:
            from .models import SecuritiesMovement
            
            quantity_change = stock.quantity - previous_value
            if quantity_change != 0:
                SecuritiesMovement.objects.create(
                    stock=stock,
                    quantity_change=quantity_change,
                    previous_quantity=previous_value,
                    new_quantity=stock.quantity,
                    movement_type="adjustment",  # Default type
                    timestamp=timezone.now(),
                    notes=f"Securities updated from {previous_value} to {stock.quantity}"
                )
        except Exception:
            # Fail silently if models don't exist yet
            pass

    def _check_reorder_point(self, stock: "Stock") -> None:
        """Check if securities has reached reorder point and trigger reorder"""
        reorder_point = int(self._get_config_value("default_reorder_point", DEFAULT_REORDER_POINT))
        
        if stock.quantity <= reorder_point:
            self._trigger_reorder_suggestion(stock)

    def _trigger_reorder_suggestion(self, stock: "Stock") -> None:
        """Generate reorder suggestion"""
        reorder_quantity = int(self._get_config_value("default_reorder_quantity", DEFAULT_REORDER_QUANTITY))
        
        # Send reorder notification
        self._send_reorder_notification(stock, reorder_quantity)

    def _send_securities_notification(self, stock: "Stock", level: str) -> None:
        """Send securities level notification"""
        notification_data = {
            "type": f"{level}_securities",
            "stock_id": stock.id,
            "product_variant": str(stock.product_variant),
            "warehouse": str(stock.warehouse),
            "current_quantity": stock.quantity,
            "level": level,
            "timestamp": timezone.now().isoformat()
        }
        
        # Send email notification
        email = self._get_config_value("notification_email")
        if email:
            self._send_email_notification(email, notification_data)
        
        # Send webhook notification
        webhook_url = self._get_config_value("webhook_url")
        if webhook_url:
            self._send_webhook_notification(webhook_url, notification_data)

    def _send_reorder_notification(self, stock: "Stock", suggested_quantity: int) -> None:
        """Send reorder notification"""
        notification_data = {
            "type": "reorder_point",
            "stock_id": stock.id,
            "product_variant": str(stock.product_variant),
            "warehouse": str(stock.warehouse),
            "current_quantity": stock.quantity,
            "suggested_reorder_quantity": suggested_quantity,
            "timestamp": timezone.now().isoformat()
        }
        
        # Send notifications
        email = self._get_config_value("notification_email")
        if email:
            self._send_email_notification(email, notification_data)
        
        webhook_url = self._get_config_value("webhook_url")
        if webhook_url:
            self._send_webhook_notification(webhook_url, notification_data)

    def _send_email_notification(self, email: str, data: Dict[str, Any]) -> None:
        """Send email notification (placeholder implementation)"""
        # This would integrate with Saleor's email system
        pass

    def _send_webhook_notification(self, webhook_url: str, data: Dict[str, Any]) -> None:
        """Send webhook notification (placeholder implementation)"""
        # This would send HTTP POST to webhook URL
        pass

    def _update_demand_forecast(self, order) -> None:
        """Update demand forecasting based on new order"""
        # Placeholder for demand forecasting logic
        pass

    def _get_config_value(self, key: str, default=None):
        """Get configuration value"""
        config = self.configuration
        for item in config:
            if item["name"] == key:
                return item["value"]
        return default

    # Public API methods
    def get_securities_report(self, warehouse_id: Optional[int] = None) -> Dict[str, Any]:
        """Generate comprehensive securities report"""
        return generate_securities_report(warehouse_id)

    def get_low_securities_items(self, warehouse_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get list of low securities items"""
        low_threshold = int(self._get_config_value("low_securities_threshold_percentage", 20))
        return check_low_securities_threshold(warehouse_id, low_threshold)

    def predict_securities_needs(self, days: Optional[int] = None) -> Dict[str, Any]:
        """Predict securities needs for specified number of days"""
        forecast_days = days or int(self._get_config_value("forecast_days", 30))
        return predict_securities_needs(forecast_days)

    def adjust_securities(
        self,
        stock_id: int,
        quantity_change: int,
        reason: str = "manual_adjustment",
        notes: str = ""
    ) -> bool:
        """Manually adjust securities quantity"""
        try:
            from ...warehouse.models import Stock
            from .models import SecuritiesMovement
            
            stock = Stock.objects.get(id=stock_id)
            previous_quantity = stock.quantity
            stock.quantity += quantity_change
            stock.save()
            
            # Log the movement
            SecuritiesMovement.objects.create(
                stock=stock,
                quantity_change=quantity_change,
                previous_quantity=previous_quantity,
                new_quantity=stock.quantity,
                movement_type=reason,
                timestamp=timezone.now(),
                notes=notes
            )
            
            return True
        except Exception:
            return False

    # Securities Master Data API methods
    def create_security_record(
        self,
        symbol: str,
        security_type: str,
        name: str,
        exchange: str = '',
        currency: str = 'USD',
        sector: str = '',
        industry: str = '',
        country: str = '',
        market_cap: Optional[int] = None,
        description: str = ''
    ) -> Optional[str]:
        """Create a new security record"""
        try:
            security = create_security(
                symbol=symbol,
                security_type=security_type,
                name=name,
                exchange=exchange,
                currency=currency,
                sector=sector,
                industry=industry,
                country=country,
                market_cap=market_cap,
                description=description
            )
            return str(security.security_id)
        except Exception:
            return None

    def get_security(self, symbol: str, security_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get security by symbol"""
        security = get_security_by_symbol(symbol, security_type)
        if security:
            return {
                'security_id': str(security.security_id),
                'symbol': security.symbol,
                'security_type': security.security_type,
                'name': security.name,
                'exchange': security.exchange,
                'currency': security.currency,
                'sector': security.sector,
                'industry': security.industry,
                'country': security.country,
                'market_cap': security.market_cap,
                'description': security.description,
                'is_active': security.is_active,
                'created_at': security.created_at.isoformat(),
                'updated_at': security.updated_at.isoformat(),
            }
        return None

    def search_securities_records(
        self,
        symbol_contains: Optional[str] = None,
        name_contains: Optional[str] = None,
        security_type: Optional[str] = None,
        exchange: Optional[str] = None,
        sector: Optional[str] = None,
        is_active: bool = True,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search securities with filters"""
        securities = search_securities(
            symbol_contains=symbol_contains,
            name_contains=name_contains,
            security_type=security_type,
            exchange=exchange,
            sector=sector,
            is_active=is_active,
            limit=limit
        )
        
        return [
            {
                'security_id': str(security.security_id),
                'symbol': security.symbol,
                'security_type': security.security_type,
                'name': security.name,
                'exchange': security.exchange,
                'currency': security.currency,
                'sector': security.sector,
                'industry': security.industry,
                'is_active': security.is_active,
            }
            for security in securities
        ]

    def get_securities_by_type_api(self, security_type: str, is_active: bool = True) -> List[Dict[str, Any]]:
        """Get securities by type"""
        securities = get_securities_by_type(security_type, is_active)
        
        return [
            {
                'security_id': str(security.security_id),
                'symbol': security.symbol,
                'name': security.name,
                'exchange': security.exchange,
                'currency': security.currency,
                'sector': security.sector,
                'industry': security.industry,
            }
            for security in securities
        ]

    def update_security_data(
        self,
        security_id: str,
        market_cap: Optional[int] = None,
        sector: Optional[str] = None,
        industry: Optional[str] = None,
        description: Optional[str] = None
    ) -> bool:
        """Update security market data"""
        return update_security_market_data(
            security_id=security_id,
            market_cap=market_cap,
            sector=sector,
            industry=industry,
            description=description
        )

    def get_securities_stats(self) -> Dict[str, Any]:
        """Get securities database statistics"""
        return get_securities_statistics()

    # Price Data API methods
    def add_security_price(
        self,
        security_id: str,
        date: str,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        volume: int,
        adjusted_close: Optional[float] = None
    ) -> bool:
        """Add daily price data for a security"""
        return add_daily_price(
            security_id=security_id,
            date=date,
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            volume=volume,
            adjusted_close=adjusted_close
        )

    def get_security_latest_price(self, security_id: str) -> Optional[Dict[str, Any]]:
        """Get latest price data for a security"""
        return get_latest_price(security_id)

    def get_security_price_history(
        self,
        security_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get price history for a security"""
        return get_price_history(
            security_id=security_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

    def get_security_price_by_date(self, security_id: str, date: str) -> Optional[Dict[str, Any]]:
        """Get price data for a specific date"""
        return get_price_by_date(security_id, date)

    def bulk_add_security_prices(self, price_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Bulk add daily price data"""
        return bulk_add_daily_prices(price_data)

    def get_security_price_stats(self, security_id: str, days: int = 30) -> Dict[str, Any]:
        """Get price statistics for a security"""
        return get_price_statistics(security_id, days)
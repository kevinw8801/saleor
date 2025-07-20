from django.core.management import call_command
from django.db import transaction
import logging

from ..base_plugin import BasePlugin, ConfigurationTypeField
from .constants import PLUGIN_ID
from .models import ProductUserAssociation


logger = logging.getLogger(__name__)


class TradexPlugin(BasePlugin):
    PLUGIN_ID = PLUGIN_ID
    PLUGIN_NAME = "Tradex"
    PLUGIN_DESCRIPTION = "Trading and exchange functionality plugin for Saleor with user tracking"
    DEFAULT_ACTIVE = True
    CONFIGURATION_PER_CHANNEL = False
    DEFAULT_CONFIGURATION = [
        {"name": "api_key", "value": None},
        {"name": "api_secret", "value": None},
        {"name": "sandbox_mode", "value": True},
        {"name": "webhook_url", "value": None},
        {"name": "auto_setup_utility_type", "value": True},
        {"name": "auto_setup_portfolio_type", "value": True},
        {"name": "track_user_actions", "value": True},
        {"name": "track_ip_addresses", "value": False},
        {"name": "default_portfolio_balance", "value": "10000"},
    ]

    CONFIG_STRUCTURE = {
        "api_key": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "API key for Tradex integration",
            "label": "API Key",
        },
        "api_secret": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "API secret for Tradex integration",
            "label": "API Secret",
        },
        "sandbox_mode": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Enable sandbox mode for testing",
            "label": "Sandbox Mode",
        },
        "webhook_url": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Webhook URL for receiving trading notifications",
            "label": "Webhook URL",
        },
        "auto_setup_utility_type": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Automatically setup Utility product type on plugin activation",
            "label": "Auto Setup Utility Type",
        },
        "auto_setup_portfolio_type": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Automatically setup Portfolio product type on plugin activation",
            "label": "Auto Setup Portfolio Type",
        },
        "track_user_actions": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Track user actions on products (create, update, delete)",
            "label": "Track User Actions",
        },
        "track_ip_addresses": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Track IP addresses of users performing actions",
            "label": "Track IP Addresses",
        },
        "default_portfolio_balance": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Default cash balance for new portfolios (in base currency)",
            "label": "Default Portfolio Balance",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Note: Don't run setup during initialization as it may cause DB issues
        # Setup will be handled by management commands when needed

    def _setup_utility_product_type(self):
        """Setup the Utility product type with trading-specific attributes."""
        try:
            with transaction.atomic():
                call_command('setup_utility_product_type')
        except Exception as e:
            # Log error but don't fail plugin initialization
            pass

    def _setup_portfolio_product_type(self):
        """Setup the Portfolio product type with operation reference attributes."""
        try:
            with transaction.atomic():
                call_command('setup_portfolio_product_type')
        except Exception as e:
            # Log error but don't fail plugin initialization
            pass

    def setup_utility_product_type(self):
        """Public method to manually setup the Utility product type."""
        call_command('setup_utility_product_type', force=True)
        return {"status": "success", "message": "Utility product type setup completed"}

    def setup_portfolio_product_type(self):
        """Public method to manually setup the Portfolio product type."""
        call_command('setup_portfolio_product_type', force=True)
        return {"status": "success", "message": "Portfolio product type setup completed"}

    def setup_all_product_types(self):
        """Public method to setup both Utility and Portfolio product types."""
        utility_result = self.setup_utility_product_type()
        portfolio_result = self.setup_portfolio_product_type()
        return {
            "status": "success", 
            "message": "All product types setup completed",
            "details": {
                "utility": utility_result,
                "portfolio": portfolio_result
            }
        }

    # Helper methods for user tracking
    def _get_config_value(self, key: str, default=None):
        """Get configuration value from the plugin configuration list."""
        for item in self.configuration:
            if item["name"] == key:
                return item["value"]
        return default

    def _should_track_actions(self):
        """Check if user action tracking is enabled."""
        return self._get_config_value("track_user_actions", True)

    def _should_track_ip(self):
        """Check if IP address tracking is enabled."""
        return self._get_config_value("track_ip_addresses", False)

    def _get_default_portfolio_balance(self):
        """Get the default portfolio balance from configuration."""
        balance_str = self._get_config_value("default_portfolio_balance", "10000")
        try:
            return float(balance_str)
        except (ValueError, TypeError):
            logger.warning(f"Invalid default_portfolio_balance value: {balance_str}, using 10000")
            return 10000.0

    def _get_user_from_requestor(self):
        """Extract user from requestor, handling both User and App instances."""
        if not self.requestor:
            return None
        
        # Handle different types of requestors
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if isinstance(self.requestor, User):
            return self.requestor
        
        # For app tokens or other non-user requestors
        return None

    def _get_context_info(self):
        """Get additional context information from the request."""
        context = {}
        
        # Try to get IP address if tracking is enabled
        if self._should_track_ip() and hasattr(self.requestor, 'META'):
            # Get IP from various headers
            x_forwarded_for = self.requestor.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                context['ip_address'] = x_forwarded_for.split(',')[0].strip()
            else:
                context['ip_address'] = self.requestor.META.get('REMOTE_ADDR')
        
        return context

    def _track_product_action(self, product, action_type, additional_context=None):
        """Internal method to track product actions."""
        if not self._should_track_actions():
            return

        try:
            user = self._get_user_from_requestor()
            context_info = self._get_context_info()
            
            # Merge additional context
            if additional_context:
                context_info.update(additional_context)
            
            # Determine source
            source = 'graphql_api'  # Default assumption
            if hasattr(self.requestor, 'META'):
                user_agent = self.requestor.META.get('HTTP_USER_AGENT', '')
                if 'admin' in user_agent.lower():
                    source = 'admin_panel'
            
            ProductUserAssociation.track_action(
                product=product,
                user=user,
                action_type=action_type,
                context_data=context_info,
                source=source,
                ip_address=context_info.get('ip_address')
            )
            
            logger.info(f"Tracked {action_type} action for product {product.id} by user {user.id if user else 'system'}")
            
        except Exception as e:
            logger.error(f"Error tracking product action: {e}")

    def _set_default_portfolio_cash_balance(self, product):
        """Set default cash balance for portfolio products."""
        try:
            # Check if this is a portfolio product
            if product.product_type and product.product_type.slug == 'portfolio':
                from ...attribute.models import Attribute, AttributeValue
                from ...attribute.utils import associate_attribute_values_to_instance
                from django.db import transaction
                
                # Get the cash attribute
                try:
                    cash_attribute = Attribute.objects.get(slug='cash')
                except Attribute.DoesNotExist:
                    logger.warning("Cash attribute not found for portfolio product")
                    return
                
                # Check if cash balance is already set for this product
                existing_values = product.attributes.filter(
                    assignment__attribute=cash_attribute
                ).exists()
                
                if not existing_values:
                    # Set default cash balance
                    default_balance = self._get_default_portfolio_balance()
                    
                    with transaction.atomic():
                        # Create the attribute value for this product
                        cash_value = AttributeValue.objects.create(
                            attribute=cash_attribute,
                            name=str(default_balance),
                            slug=f"{product.id}_{cash_attribute.id}",
                        )
                        
                        # Associate the value with the product
                        associate_attribute_values_to_instance(
                            product, 
                            {cash_attribute.id: [cash_value]}
                        )
                        
                        logger.info(f"Set default cash balance {default_balance} for portfolio product {product.id}")
        except Exception as e:
            logger.error(f"Error setting default portfolio cash balance: {e}")

    # Plugin hook methods for product tracking
    def product_created(self, product, previous_value=None, webhooks=None):
        """Hook called when a product is created."""
        # Set default cash balance for portfolio products
        self._set_default_portfolio_cash_balance(product)
        
        # Track the product creation
        self._track_product_action(
            product=product,
            action_type='created',
            additional_context={
                'product_type': product.product_type.name if product.product_type else None,
                'category': product.category.name if product.category else None,
            }
        )
        return previous_value

    def product_updated(self, product, previous_value=None, webhooks=None):
        """Hook called when a product is updated."""
        self._track_product_action(
            product=product,
            action_type='updated',
            additional_context={
                'updated_fields': getattr(product, '_dirty_fields', [])
            }
        )
        return previous_value

    def product_deleted(self, product, product_ids, previous_value=None, webhooks=None):
        """Hook called when products are deleted."""
        # For bulk deletes, product_ids contains the IDs
        if product_ids:
            for product_id in product_ids:
                try:
                    # Create a mock product object for tracking
                    product_obj = type('Product', (), {'id': product_id, 'name': f'Product {product_id}'})()
                    self._track_product_action(
                        product=product_obj,
                        action_type='deleted',
                        additional_context={'bulk_delete': True, 'total_deleted': len(product_ids)}
                    )
                except Exception as e:
                    logger.error(f"Error tracking delete for product {product_id}: {e}")
        elif product:
            self._track_product_action(
                product=product,
                action_type='deleted'
            )
        return previous_value

    def product_variant_created(self, product_variant, previous_value=None, webhooks=None):
        """Hook called when a product variant is created."""
        if product_variant.product:
            self._track_product_action(
                product=product_variant.product,
                action_type='variant_created',
                additional_context={
                    'variant_id': product_variant.id,
                    'variant_sku': product_variant.sku,
                    'variant_name': product_variant.name
                }
            )
        return previous_value

    def product_variant_updated(self, product_variant, previous_value=None, webhooks=None):
        """Hook called when a product variant is updated."""
        if product_variant.product:
            self._track_product_action(
                product=product_variant.product,
                action_type='variant_updated',
                additional_context={
                    'variant_id': product_variant.id,
                    'variant_sku': product_variant.sku,
                    'updated_fields': getattr(product_variant, '_dirty_fields', [])
                }
            )
        return previous_value

    def product_variant_deleted(self, product_variant, previous_value=None, webhooks=None):
        """Hook called when a product variant is deleted."""
        if product_variant.product:
            self._track_product_action(
                product=product_variant.product,
                action_type='variant_deleted',
                additional_context={
                    'variant_id': product_variant.id,
                    'variant_sku': product_variant.sku
                }
            )
        return previous_value

    def product_media_created(self, product_media, previous_value=None, webhooks=None):
        """Hook called when product media is created."""
        if product_media.product:
            self._track_product_action(
                product=product_media.product,
                action_type='media_created',
                additional_context={
                    'media_id': product_media.id,
                    'media_type': product_media.type,
                    'media_url': product_media.image.url if product_media.image else None
                }
            )
        return previous_value

    def product_media_updated(self, product_media, previous_value=None, webhooks=None):
        """Hook called when product media is updated."""
        if product_media.product:
            self._track_product_action(
                product=product_media.product,
                action_type='media_updated',
                additional_context={
                    'media_id': product_media.id,
                    'media_type': product_media.type
                }
            )
        return previous_value

    def product_media_deleted(self, product_media, previous_value=None, webhooks=None):
        """Hook called when product media is deleted."""
        if product_media.product:
            self._track_product_action(
                product=product_media.product,
                action_type='media_deleted',
                additional_context={
                    'media_id': product_media.id,
                    'media_type': product_media.type
                }
            )
        return previous_value

    # Utility methods for querying user associations
    def get_user_created_products(self, user):
        """Get all products created by a specific user."""
        return ProductUserAssociation.get_user_products(user, action_type='created')

    def get_product_creator(self, product):
        """Get the user who created a specific product."""
        return ProductUserAssociation.get_product_creator(product)

    def get_product_activity_history(self, product):
        """Get the complete activity history for a product."""
        return ProductUserAssociation.get_product_history(product)
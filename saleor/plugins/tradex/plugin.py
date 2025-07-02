from django.core.management import call_command
from django.db import transaction

from ..base_plugin import BasePlugin, ConfigurationTypeField
from .constants import PLUGIN_ID


class TradexPlugin(BasePlugin):
    PLUGIN_ID = PLUGIN_ID
    PLUGIN_NAME = "Tradex"
    PLUGIN_DESCRIPTION = "Trading and exchange functionality plugin for Saleor"
    DEFAULT_ACTIVE = True
    CONFIGURATION_PER_CHANNEL = False
    DEFAULT_CONFIGURATION = [
        {"name": "api_key", "value": None},
        {"name": "api_secret", "value": None},
        {"name": "sandbox_mode", "value": True},
        {"name": "webhook_url", "value": None},
        {"name": "auto_setup_utility_type", "value": True},
        {"name": "auto_setup_portfolio_type", "value": True},
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
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Setup product types if auto-setup is enabled and plugin is active
        if self.active:
            config = self.get_plugin_configuration()
            if config.get("auto_setup_utility_type", True):
                self._setup_utility_product_type()
            if config.get("auto_setup_portfolio_type", True):
                self._setup_portfolio_product_type()

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
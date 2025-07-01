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
    }
from django.apps import AppConfig


class TradexConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'saleor.plugins.tradex'
    label = 'tradex'
    verbose_name = 'Tradex Plugin'
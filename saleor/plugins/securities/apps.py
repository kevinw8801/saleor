from django.apps import AppConfig


class SecuritiesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'saleor.plugins.securities'
    verbose_name = 'Securities Plugin'

    def ready(self):
        """
        Called when the app is ready. This is where we can perform startup tasks.
        """
        # Don't run startup logic during migrations or static file collection
        import sys
        if any(arg in sys.argv for arg in ['migrate', 'makemigrations', 'collectstatic', 'test']):
            return
        
        # Import here to avoid circular imports
        from .startup import initialize_tickers_data
        
        # Run ticker initialization in a separate thread to avoid blocking startup
        # Add a small delay to ensure all apps are fully loaded
        import threading
        import time
        
        def delayed_initialization():
            time.sleep(5)  # Wait 5 seconds for all apps to be ready
            initialize_tickers_data()
        
        threading.Thread(target=delayed_initialization, daemon=True).start()
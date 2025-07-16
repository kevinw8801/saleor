from django.apps import AppConfig


class PolygonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'saleor.polygon'
    verbose_name = 'Polygon Integration'
    
    def ready(self):
        """
        Called when the app is ready. Initialize ticker data here.
        """
        # Import the securities startup logic
        from ..plugins.securities.startup import initialize_tickers_data
        
        # Run ticker initialization in a separate thread with delay
        import threading
        import time
        
        def delayed_initialization():
            time.sleep(10)  # Wait 10 seconds for all apps to be ready
            initialize_tickers_data()
        
        threading.Thread(target=delayed_initialization, daemon=True).start()
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
        
        # Run ticker initialization in a separate thread with delay and retry
        import threading
        import time
        
        def delayed_initialization_with_retry():
            # Wait longer for migrations to complete
            time.sleep(30)  # Wait 30 seconds for migrations to complete
            
            # Retry logic in case migrations are still running
            max_retries = 5
            retry_delay = 60  # 1 minute between retries
            
            for attempt in range(max_retries):
                try:
                    initialize_tickers_data()
                    break  # Success, exit retry loop
                except Exception as e:
                    if "does not exist" in str(e) and attempt < max_retries - 1:
                        print(f"Ticker initialization attempt {attempt + 1} failed, retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        print(f"Ticker initialization failed after {attempt + 1} attempts: {e}")
                        break
        
        threading.Thread(target=delayed_initialization_with_retry, daemon=True).start()
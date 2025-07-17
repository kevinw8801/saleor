# Generated for securities plugin - Initial migration
# This migration handles the case where tables may already exist from polygon app

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


def check_and_create_tables(apps, schema_editor):
    """Check if tables already exist and create only if they don't"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Define tables that might already exist
        tables_to_check = [
            'tickers',
            'securities_alert',
            'securities_batch', 
            'securities_forecast',
            'securities_movement',
            'securities_settings',
            'securities_reorder_suggestion'
        ]
        
        existing_tables = []
        
        # Check which tables already exist
        for table_name in tables_to_check:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                );
            """, [table_name])
            if cursor.fetchone()[0]:
                existing_tables.append(table_name)
                
        print(f"Found existing tables: {existing_tables}")
        
        # Create tickers table if it doesn't exist
        if 'tickers' not in existing_tables:
            cursor.execute("""
                CREATE TABLE tickers (
                    ticker VARCHAR(10) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    type VARCHAR(10) NOT NULL,
                    exchange VARCHAR(10) NOT NULL,
                    active BOOLEAN NOT NULL DEFAULT TRUE,
                    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                );
            """)
            
            # Create indexes for tickers
            cursor.execute("CREATE INDEX idx_ticker_search ON tickers (ticker, name);")
            cursor.execute("CREATE INDEX securities_tickers_type_idx ON tickers (type);")
            cursor.execute("CREATE INDEX securities_tickers_exchange_idx ON tickers (exchange);")
            cursor.execute("CREATE INDEX securities_tickers_active_idx ON tickers (active);")
            print("Created tickers table")
        else:
            print("tickers table already exists, skipping creation")


def reverse_check_and_create_tables(apps, schema_editor):
    """Reverse operation - don't drop tables as they might be used by other apps"""
    pass


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('warehouse', '0001_initial'),
    ]

    operations = [
        # Check and create tables if they don't exist
        migrations.RunPython(check_and_create_tables, reverse_check_and_create_tables),
        
        # Create models that don't have table conflicts - only if table doesn't exist
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS securities_alert (
                    id SERIAL PRIMARY KEY,
                    alert_type VARCHAR(20) NOT NULL,
                    message TEXT NOT NULL,
                    quantity_at_alert INTEGER NOT NULL,
                    threshold INTEGER,
                    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
                    resolved_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    stock_id INTEGER NOT NULL REFERENCES warehouse_stock(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS securities_alert_stock_alert_type_idx ON securities_alert (stock_id, alert_type);
                CREATE INDEX IF NOT EXISTS securities_alert_is_resolved_created_at_idx ON securities_alert (is_resolved, created_at);
            """,
            reverse_sql="DROP TABLE IF EXISTS securities_alert CASCADE;"
        ),
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS securities_batch (
                    id SERIAL PRIMARY KEY,
                    batch_number VARCHAR(100) NOT NULL,
                    quantity INTEGER NOT NULL CHECK (quantity >= 0),
                    cost_per_unit DECIMAL(12, 4),
                    expiry_date DATE,
                    received_date DATE NOT NULL DEFAULT CURRENT_DATE,
                    supplier_reference VARCHAR(255),
                    is_expired BOOLEAN NOT NULL DEFAULT FALSE,
                    notes TEXT,
                    stock_id INTEGER NOT NULL REFERENCES warehouse_stock(id) ON DELETE CASCADE,
                    UNIQUE(stock_id, batch_number)
                );
                CREATE INDEX IF NOT EXISTS securities_batch_stock_expiry_date_idx ON securities_batch (stock_id, expiry_date);
                CREATE INDEX IF NOT EXISTS securities_batch_expiry_date_is_expired_idx ON securities_batch (expiry_date, is_expired);
            """,
            reverse_sql="DROP TABLE IF EXISTS securities_batch CASCADE;"
        ),
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS securities_forecast (
                    id SERIAL PRIMARY KEY,
                    forecast_date DATE NOT NULL,
                    predicted_demand INTEGER NOT NULL CHECK (predicted_demand >= 0),
                    confidence_level DECIMAL(5, 2) NOT NULL CHECK (confidence_level >= 0),
                    actual_demand INTEGER CHECK (actual_demand >= 0),
                    forecast_method VARCHAR(50) NOT NULL DEFAULT 'moving_average',
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    stock_id INTEGER NOT NULL REFERENCES warehouse_stock(id) ON DELETE CASCADE,
                    UNIQUE(stock_id, forecast_date, forecast_method)
                );
                CREATE INDEX IF NOT EXISTS securities_forecast_stock_forecast_date_idx ON securities_forecast (stock_id, forecast_date);
                CREATE INDEX IF NOT EXISTS securities_forecast_forecast_date_idx ON securities_forecast (forecast_date);
            """,
            reverse_sql="DROP TABLE IF EXISTS securities_forecast CASCADE;"
        ),
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS securities_movement (
                    id SERIAL PRIMARY KEY,
                    quantity_change INTEGER NOT NULL,
                    previous_quantity INTEGER NOT NULL,
                    new_quantity INTEGER NOT NULL,
                    movement_type VARCHAR(20) NOT NULL DEFAULT 'adjustment',
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    notes TEXT,
                    reference_order VARCHAR(100),
                    created_by VARCHAR(255),
                    stock_id INTEGER NOT NULL REFERENCES warehouse_stock(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS securities_movement_stock_timestamp_idx ON securities_movement (stock_id, timestamp);
                CREATE INDEX IF NOT EXISTS securities_movement_movement_type_timestamp_idx ON securities_movement (movement_type, timestamp);
            """,
            reverse_sql="DROP TABLE IF EXISTS securities_movement CASCADE;"
        ),
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS securities_settings (
                    id SERIAL PRIMARY KEY,
                    reorder_point INTEGER NOT NULL CHECK (reorder_point >= 0),
                    reorder_quantity INTEGER NOT NULL CHECK (reorder_quantity >= 1),
                    safety_stock INTEGER NOT NULL DEFAULT 0 CHECK (safety_stock >= 0),
                    max_stock_level INTEGER CHECK (max_stock_level >= 1),
                    lead_time_days INTEGER NOT NULL DEFAULT 7 CHECK (lead_time_days >= 0),
                    enable_auto_reorder BOOLEAN NOT NULL DEFAULT FALSE,
                    track_expiry BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    stock_id INTEGER NOT NULL UNIQUE REFERENCES warehouse_stock(id) ON DELETE CASCADE
                );
            """,
            reverse_sql="DROP TABLE IF EXISTS securities_settings CASCADE;"
        ),
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS securities_reorder_suggestion (
                    id SERIAL PRIMARY KEY,
                    suggested_quantity INTEGER NOT NULL CHECK (suggested_quantity >= 1),
                    reason TEXT NOT NULL,
                    urgency_level VARCHAR(20) NOT NULL DEFAULT 'medium',
                    estimated_cost DECIMAL(12, 2),
                    is_approved BOOLEAN NOT NULL DEFAULT FALSE,
                    is_processed BOOLEAN NOT NULL DEFAULT FALSE,
                    approved_by VARCHAR(255),
                    processed_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    stock_id INTEGER NOT NULL REFERENCES warehouse_stock(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS securities_reorder_suggestion_stock_is_processed_idx ON securities_reorder_suggestion (stock_id, is_processed);
                CREATE INDEX IF NOT EXISTS securities_reorder_suggestion_urgency_level_created_at_idx ON securities_reorder_suggestion (urgency_level, created_at);
            """,
            reverse_sql="DROP TABLE IF EXISTS securities_reorder_suggestion CASCADE;"
        ),
    ]
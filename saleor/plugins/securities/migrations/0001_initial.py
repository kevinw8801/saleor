# Generated for securities plugin - Initial migration

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('warehouse', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tickers',
            fields=[
                ('ticker', models.CharField(help_text='Ticker symbol (e.g., AAPL, SPY)', max_length=10, primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='Company/fund name', max_length=255)),
                ('type', models.CharField(choices=[('cs', 'Common Stock'), ('etp', 'Exchange Traded Product')], help_text="Type of security - 'cs' for stock, 'etp' for ETF", max_length=10)),
                ('exchange', models.CharField(help_text='Exchange where the ticker is traded', max_length=10)),
                ('active', models.BooleanField(default=True, help_text='Whether the ticker is actively traded')),
                ('last_updated', models.DateTimeField(auto_now=True, help_text='Timestamp of last update')),
            ],
            options={
                'verbose_name': 'Ticker',
                'verbose_name_plural': 'Tickers',
                'db_table': 'tickers',
                'ordering': ['ticker'],
            },
        ),
        migrations.CreateModel(
            name='SecuritiesAlert',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alert_type', models.CharField(choices=[('low_securities', 'Low Securities'), ('out_of_securities', 'Out Of Securities'), ('reorder_point', 'Reorder Point'), ('overstocked', 'Overstocked')], max_length=20)),
                ('message', models.TextField()),
                ('quantity_at_alert', models.IntegerField()),
                ('threshold', models.IntegerField(blank=True, null=True)),
                ('is_resolved', models.BooleanField(default=False)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('stock', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='securities_alerts', to='warehouse.stock')),
            ],
            options={
                'db_table': 'securities_alert',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SecuritiesBatch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('batch_number', models.CharField(max_length=100)),
                ('quantity', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('cost_per_unit', models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True)),
                ('expiry_date', models.DateField(blank=True, null=True)),
                ('received_date', models.DateField(auto_now_add=True)),
                ('supplier_reference', models.CharField(blank=True, max_length=255)),
                ('is_expired', models.BooleanField(default=False)),
                ('notes', models.TextField(blank=True)),
                ('stock', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='securities_batches', to='warehouse.stock')),
            ],
            options={
                'db_table': 'securities_batch',
                'ordering': ['expiry_date', 'received_date'],
            },
        ),
        migrations.CreateModel(
            name='SecuritiesForecast',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('forecast_date', models.DateField()),
                ('predicted_demand', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('confidence_level', models.DecimalField(decimal_places=2, help_text='Confidence level as percentage (0-100)', max_digits=5, validators=[django.core.validators.MinValueValidator(0)])),
                ('actual_demand', models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ('forecast_method', models.CharField(default='moving_average', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('stock', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='securities_forecasts', to='warehouse.stock')),
            ],
            options={
                'db_table': 'securities_forecast',
                'ordering': ['-forecast_date'],
            },
        ),
        migrations.CreateModel(
            name='SecuritiesMovement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity_change', models.IntegerField(help_text='Positive for increase, negative for decrease')),
                ('previous_quantity', models.IntegerField()),
                ('new_quantity', models.IntegerField()),
                ('movement_type', models.CharField(choices=[('adjustment', 'Adjustment'), ('purchase', 'Purchase'), ('sale', 'Sale'), ('return', 'Return'), ('transfer', 'Transfer'), ('damaged', 'Damaged'), ('expired', 'Expired')], default='adjustment', max_length=20)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('notes', models.TextField(blank=True)),
                ('reference_order', models.CharField(blank=True, max_length=100)),
                ('created_by', models.CharField(blank=True, max_length=255)),
                ('stock', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='securities_movements', to='warehouse.stock')),
            ],
            options={
                'db_table': 'securities_movement',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='SecuritiesSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reorder_point', models.IntegerField(help_text='Quantity threshold to trigger reorder', validators=[django.core.validators.MinValueValidator(0)])),
                ('reorder_quantity', models.IntegerField(help_text='Quantity to order when reorder point is reached', validators=[django.core.validators.MinValueValidator(1)])),
                ('safety_stock', models.IntegerField(default=0, help_text='Safety securities buffer quantity', validators=[django.core.validators.MinValueValidator(0)])),
                ('max_stock_level', models.IntegerField(blank=True, help_text='Maximum securities level before overstock alert', null=True, validators=[django.core.validators.MinValueValidator(1)])),
                ('lead_time_days', models.IntegerField(default=7, help_text='Lead time for restocking in days', validators=[django.core.validators.MinValueValidator(0)])),
                ('enable_auto_reorder', models.BooleanField(default=False, help_text='Enable automatic reorder suggestions')),
                ('track_expiry', models.BooleanField(default=False, help_text='Track expiry dates for this securities')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('stock', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='securities_settings', to='warehouse.stock')),
            ],
            options={
                'db_table': 'securities_settings',
            },
        ),
        migrations.CreateModel(
            name='ReorderSuggestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('suggested_quantity', models.IntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ('reason', models.TextField()),
                ('urgency_level', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='medium', max_length=20)),
                ('estimated_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('is_approved', models.BooleanField(default=False)),
                ('is_processed', models.BooleanField(default=False)),
                ('approved_by', models.CharField(blank=True, max_length=255)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('stock', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='securities_reorder_suggestions', to='warehouse.stock')),
            ],
            options={
                'db_table': 'securities_reorder_suggestion',
                'ordering': ['-created_at'],
            },
        ),
        # Add indexes for Tickers
        migrations.AddIndex(
            model_name='tickers',
            index=models.Index(fields=['ticker', 'name'], name='idx_ticker_search'),
        ),
        migrations.AddIndex(
            model_name='tickers',
            index=models.Index(fields=['type'], name='securities_tickers_type_idx'),
        ),
        migrations.AddIndex(
            model_name='tickers',
            index=models.Index(fields=['exchange'], name='securities_tickers_exchange_idx'),
        ),
        migrations.AddIndex(
            model_name='tickers',
            index=models.Index(fields=['active'], name='securities_tickers_active_idx'),
        ),
        # Add indexes for SecuritiesAlert
        migrations.AddIndex(
            model_name='securitiesalert',
            index=models.Index(fields=['stock', 'alert_type'], name='securities_alert_stock_alert_type_idx'),
        ),
        migrations.AddIndex(
            model_name='securitiesalert',
            index=models.Index(fields=['is_resolved', 'created_at'], name='securities_alert_is_resolved_created_at_idx'),
        ),
        # Add indexes for SecuritiesBatch
        migrations.AddIndex(
            model_name='securitiesbatch',
            index=models.Index(fields=['stock', 'expiry_date'], name='securities_batch_stock_expiry_date_idx'),
        ),
        migrations.AddIndex(
            model_name='securitiesbatch',
            index=models.Index(fields=['expiry_date', 'is_expired'], name='securities_batch_expiry_date_is_expired_idx'),
        ),
        # Add indexes for SecuritiesForecast
        migrations.AddIndex(
            model_name='securitiesforecast',
            index=models.Index(fields=['stock', 'forecast_date'], name='securities_forecast_stock_forecast_date_idx'),
        ),
        migrations.AddIndex(
            model_name='securitiesforecast',
            index=models.Index(fields=['forecast_date'], name='securities_forecast_forecast_date_idx'),
        ),
        # Add indexes for SecuritiesMovement
        migrations.AddIndex(
            model_name='securitiesmovement',
            index=models.Index(fields=['stock', 'timestamp'], name='securities_movement_stock_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='securitiesmovement',
            index=models.Index(fields=['movement_type', 'timestamp'], name='securities_movement_movement_type_timestamp_idx'),
        ),
        # Add indexes for ReorderSuggestion
        migrations.AddIndex(
            model_name='reordersuggestion',
            index=models.Index(fields=['stock', 'is_processed'], name='securities_reorder_suggestion_stock_is_processed_idx'),
        ),
        migrations.AddIndex(
            model_name='reordersuggestion',
            index=models.Index(fields=['urgency_level', 'created_at'], name='securities_reorder_suggestion_urgency_level_created_at_idx'),
        ),
        # Add unique constraints
        migrations.AlterUniqueTogether(
            name='securitiesbatch',
            unique_together={('stock', 'batch_number')},
        ),
        migrations.AlterUniqueTogether(
            name='securitiesforecast',
            unique_together={('stock', 'forecast_date', 'forecast_method')},
        ),
    ]
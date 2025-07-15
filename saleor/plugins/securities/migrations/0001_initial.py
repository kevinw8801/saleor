# Generated manually for securities plugin

import uuid
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('warehouse', '0001_initial'),  # Assuming warehouse app exists
    ]

    operations = [
        migrations.CreateModel(
            name='Securities',
            fields=[
                ('security_id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='Unique identifier for the security', primary_key=True, serialize=False)),
                ('symbol', models.CharField(help_text='Trading symbol for the security', max_length=16)),
                ('security_type', models.CharField(choices=[('STOCK', 'Stock'), ('ETF', 'ETF'), ('MUTUAL_FUND', 'Mutual Fund'), ('BOND', 'Bond'), ('OPTION', 'Option'), ('FUTURE', 'Future'), ('CRYPTO', 'Cryptocurrency'), ('FOREX', 'Forex'), ('COMMODITY', 'Commodity'), ('INDEX', 'Index')], help_text='Type of security (stock, ETF, etc.)', max_length=12)),
                ('name', models.CharField(help_text='Full name of the security', max_length=255)),
                ('exchange', models.CharField(blank=True, help_text='Exchange where the security is traded', max_length=10)),
                ('currency', models.CharField(default='USD', help_text='Currency of the security', max_length=3)),
                ('sector', models.CharField(blank=True, help_text='Business sector', max_length=50)),
                ('industry', models.CharField(blank=True, help_text='Industry classification', max_length=50)),
                ('country', models.CharField(blank=True, help_text='Country code (ISO 3166-1 alpha-3)', max_length=3)),
                ('market_cap', models.BigIntegerField(blank=True, help_text='Market capitalization in base currency', null=True)),
                ('description', models.TextField(blank=True, help_text='Description of the security')),
                ('is_active', models.BooleanField(default=True, help_text='Whether the security is actively traded')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='When the security record was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='When the security record was last updated')),
            ],
            options={
                'verbose_name': 'Security',
                'verbose_name_plural': 'Securities',
                'db_table': 'securities',
                'ordering': ['symbol'],
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
        migrations.AddIndex(
            model_name='securities',
            index=models.Index(fields=['symbol'], name='securities_symbol_idx'),
        ),
        migrations.AddIndex(
            model_name='securities',
            index=models.Index(fields=['security_type'], name='securities_security_type_idx'),
        ),
        migrations.AddIndex(
            model_name='securities',
            index=models.Index(fields=['exchange'], name='securities_exchange_idx'),
        ),
        migrations.AddIndex(
            model_name='securities',
            index=models.Index(fields=['sector'], name='securities_sector_idx'),
        ),
        migrations.AddIndex(
            model_name='securities',
            index=models.Index(fields=['is_active'], name='securities_is_active_idx'),
        ),
        migrations.AddIndex(
            model_name='securities',
            index=models.Index(fields=['created_at'], name='securities_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='securitiesalert',
            index=models.Index(fields=['stock', 'alert_type'], name='securities_alert_stock_alert_type_idx'),
        ),
        migrations.AddIndex(
            model_name='securitiesalert',
            index=models.Index(fields=['is_resolved', 'created_at'], name='securities_alert_is_resolved_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='securitiesbatch',
            index=models.Index(fields=['stock', 'expiry_date'], name='securities_batch_stock_expiry_date_idx'),
        ),
        migrations.AddIndex(
            model_name='securitiesbatch',
            index=models.Index(fields=['expiry_date', 'is_expired'], name='securities_batch_expiry_date_is_expired_idx'),
        ),
        migrations.AddIndex(
            model_name='securitiesforecast',
            index=models.Index(fields=['stock', 'forecast_date'], name='securities_forecast_stock_forecast_date_idx'),
        ),
        migrations.AddIndex(
            model_name='securitiesforecast',
            index=models.Index(fields=['forecast_date'], name='securities_forecast_forecast_date_idx'),
        ),
        migrations.AddIndex(
            model_name='securitiesmovement',
            index=models.Index(fields=['stock', 'timestamp'], name='securities_movement_stock_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='securitiesmovement',
            index=models.Index(fields=['movement_type', 'timestamp'], name='securities_movement_movement_type_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='reordersuggestion',
            index=models.Index(fields=['stock', 'is_processed'], name='securities_reorder_suggestion_stock_is_processed_idx'),
        ),
        migrations.AddIndex(
            model_name='reordersuggestion',
            index=models.Index(fields=['urgency_level', 'created_at'], name='securities_reorder_suggestion_urgency_level_created_at_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='securities',
            unique_together={('symbol', 'security_type')},
        ),
        migrations.AlterUniqueTogether(
            name='securitiesbatch',
            unique_together={('stock', 'batch_number')},
        ),
        migrations.AlterUniqueTogether(
            name='securitiesforecast',
            unique_together={('stock', 'forecast_date', 'forecast_method')},
        ),
    ]
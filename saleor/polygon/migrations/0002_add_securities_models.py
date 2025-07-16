# Generated manually for polygon app - Add Securities and SecurityDailyPrices models

import uuid
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('polygon', '0001_initial'),
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
            name='SecurityDailyPrices',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(help_text='Trading date')),
                ('close_price', models.DecimalField(decimal_places=4, help_text='Closing price for the day', max_digits=18)),
                ('open_price', models.DecimalField(decimal_places=4, help_text='Opening price for the day', max_digits=18)),
                ('high_price', models.DecimalField(decimal_places=4, help_text='Highest price for the day', max_digits=18)),
                ('low_price', models.DecimalField(decimal_places=4, help_text='Lowest price for the day', max_digits=18)),
                ('volume', models.BigIntegerField(help_text='Trading volume for the day', validators=[django.core.validators.MinValueValidator(0)])),
                ('adjusted_close', models.DecimalField(blank=True, decimal_places=4, help_text='Adjusted closing price (for splits, dividends, etc.)', max_digits=18, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='When this price record was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='When this price record was last updated')),
                ('security', models.ForeignKey(help_text='Reference to the security', on_delete=django.db.models.deletion.CASCADE, related_name='daily_prices', to='polygon.securities')),
            ],
            options={
                'verbose_name': 'Security Daily Price',
                'verbose_name_plural': 'Security Daily Prices',
                'db_table': 'security_daily_prices',
                'ordering': ['-date', 'security__symbol'],
            },
        ),
        # Add indexes for Securities
        migrations.AddIndex(
            model_name='securities',
            index=models.Index(fields=['symbol'], name='polygon_securities_symbol_idx'),
        ),
        migrations.AddIndex(
            model_name='securities',
            index=models.Index(fields=['security_type'], name='polygon_securities_type_idx'),
        ),
        migrations.AddIndex(
            model_name='securities',
            index=models.Index(fields=['exchange'], name='polygon_securities_exchange_idx'),
        ),
        migrations.AddIndex(
            model_name='securities',
            index=models.Index(fields=['sector'], name='polygon_securities_sector_idx'),
        ),
        migrations.AddIndex(
            model_name='securities',
            index=models.Index(fields=['is_active'], name='polygon_securities_active_idx'),
        ),
        migrations.AddIndex(
            model_name='securities',
            index=models.Index(fields=['created_at'], name='polygon_securities_created_idx'),
        ),
        # Add indexes for SecurityDailyPrices
        migrations.AddIndex(
            model_name='securitydailyprices',
            index=models.Index(fields=['security', 'date'], name='polygon_security_daily_prices_security_date_idx'),
        ),
        migrations.AddIndex(
            model_name='securitydailyprices',
            index=models.Index(fields=['date'], name='polygon_security_daily_prices_date_idx'),
        ),
        migrations.AddIndex(
            model_name='securitydailyprices',
            index=models.Index(fields=['security', '-date'], name='polygon_security_daily_prices_security_date_desc_idx'),
        ),
        migrations.AddIndex(
            model_name='securitydailyprices',
            index=models.Index(fields=['volume'], name='polygon_security_daily_prices_volume_idx'),
        ),
        # Add unique constraints
        migrations.AlterUniqueTogether(
            name='securities',
            unique_together={('symbol', 'security_type')},
        ),
        migrations.AlterUniqueTogether(
            name='securitydailyprices',
            unique_together={('security', 'date')},
        ),
    ]
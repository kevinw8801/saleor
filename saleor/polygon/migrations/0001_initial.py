# Generated manually for polygon app - Initial migration

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
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
            name='FinancialInstrument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(max_length=50, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('instrument_type', models.CharField(choices=[('STOCK', 'Stock'), ('OPTION', 'Option'), ('CRYPTO', 'Cryptocurrency'), ('FOREX', 'Foreign Exchange')], max_length=10)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'polygon_financial_instrument',
                'ordering': ['symbol'],
            },
        ),
        migrations.CreateModel(
            name='MarketDataCache',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cache_key', models.CharField(max_length=255, unique=True)),
                ('data', models.JSONField()),
                ('expires_at', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'polygon_market_data_cache',
            },
        ),
        migrations.CreateModel(
            name='PolygonContract',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contract_address', models.CharField(max_length=42, unique=True)),
                ('contract_type', models.CharField(choices=[('ERC20', 'ERC-20 Token'), ('ERC721', 'ERC-721 NFT'), ('ERC1155', 'ERC-1155 Multi Token'), ('CUSTOM', 'Custom Contract')], max_length=10)),
                ('name', models.CharField(max_length=255)),
                ('symbol', models.CharField(blank=True, max_length=50)),
                ('decimals', models.IntegerField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'polygon_contract',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='PolygonTransaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_id', models.CharField(max_length=255, unique=True)),
                ('block_number', models.BigIntegerField()),
                ('transaction_hash', models.CharField(max_length=66)),
                ('from_address', models.CharField(max_length=42)),
                ('to_address', models.CharField(max_length=42)),
                ('value', models.DecimalField(decimal_places=18, max_digits=36)),
                ('gas_used', models.BigIntegerField()),
                ('gas_price', models.DecimalField(decimal_places=18, max_digits=36)),
                ('status', models.CharField(default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'polygon_transaction',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PolygonWallet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wallet_address', models.CharField(max_length=42, unique=True)),
                ('label', models.CharField(blank=True, max_length=255)),
                ('is_monitored', models.BooleanField(default=False)),
                ('balance', models.DecimalField(decimal_places=18, default=0, max_digits=36)),
                ('last_sync', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'polygon_wallet',
                'ordering': ['wallet_address'],
            },
        ),
        migrations.CreateModel(
            name='StockData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField()),
                ('open_price', models.DecimalField(decimal_places=8, max_digits=20)),
                ('high_price', models.DecimalField(decimal_places=8, max_digits=20)),
                ('low_price', models.DecimalField(decimal_places=8, max_digits=20)),
                ('close_price', models.DecimalField(decimal_places=8, max_digits=20)),
                ('volume', models.BigIntegerField()),
                ('vwap', models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True)),
                ('market_cap', models.DecimalField(blank=True, decimal_places=2, max_digits=30, null=True)),
                ('pe_ratio', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('dividend_yield', models.DecimalField(blank=True, decimal_places=4, max_digits=5, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('instrument', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stock_data', to='polygon.financialinstrument')),
            ],
            options={
                'db_table': 'polygon_stock_data',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='OptionData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('option_symbol', models.CharField(max_length=50, unique=True)),
                ('option_type', models.CharField(choices=[('CALL', 'Call Option'), ('PUT', 'Put Option')], max_length=4)),
                ('strike_price', models.DecimalField(decimal_places=8, max_digits=20)),
                ('expiration_date', models.DateField()),
                ('timestamp', models.DateTimeField()),
                ('bid_price', models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True)),
                ('ask_price', models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True)),
                ('last_price', models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True)),
                ('volume', models.BigIntegerField(default=0)),
                ('open_interest', models.BigIntegerField(default=0)),
                ('implied_volatility', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('delta', models.DecimalField(blank=True, decimal_places=5, max_digits=6, null=True)),
                ('gamma', models.DecimalField(blank=True, decimal_places=5, max_digits=6, null=True)),
                ('theta', models.DecimalField(blank=True, decimal_places=5, max_digits=6, null=True)),
                ('vega', models.DecimalField(blank=True, decimal_places=5, max_digits=6, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('underlying_instrument', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='polygon.financialinstrument')),
            ],
            options={
                'db_table': 'polygon_option_data',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='ForexData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField()),
                ('open_rate', models.DecimalField(decimal_places=8, max_digits=20)),
                ('high_rate', models.DecimalField(decimal_places=8, max_digits=20)),
                ('low_rate', models.DecimalField(decimal_places=8, max_digits=20)),
                ('close_rate', models.DecimalField(decimal_places=8, max_digits=20)),
                ('volume', models.DecimalField(blank=True, decimal_places=8, max_digits=30, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('instrument', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='forex_data', to='polygon.financialinstrument')),
            ],
            options={
                'db_table': 'polygon_forex_data',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='CryptoData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField()),
                ('open_price', models.DecimalField(decimal_places=8, max_digits=20)),
                ('high_price', models.DecimalField(decimal_places=8, max_digits=20)),
                ('low_price', models.DecimalField(decimal_places=8, max_digits=20)),
                ('close_price', models.DecimalField(decimal_places=8, max_digits=20)),
                ('volume', models.DecimalField(decimal_places=8, max_digits=30)),
                ('market_cap', models.DecimalField(blank=True, decimal_places=2, max_digits=30, null=True)),
                ('circulating_supply', models.DecimalField(blank=True, decimal_places=8, max_digits=30, null=True)),
                ('total_supply', models.DecimalField(blank=True, decimal_places=8, max_digits=30, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('instrument', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='crypto_data', to='polygon.financialinstrument')),
            ],
            options={
                'db_table': 'polygon_crypto_data',
                'ordering': ['-timestamp'],
            },
        ),
        # Add indexes
        migrations.AddIndex(
            model_name='tickers',
            index=models.Index(fields=['ticker', 'name'], name='idx_ticker_search'),
        ),
        migrations.AddIndex(
            model_name='tickers',
            index=models.Index(fields=['type'], name='polygon_tickers_type_idx'),
        ),
        migrations.AddIndex(
            model_name='tickers',
            index=models.Index(fields=['exchange'], name='polygon_tickers_exchange_idx'),
        ),
        migrations.AddIndex(
            model_name='tickers',
            index=models.Index(fields=['active'], name='polygon_tickers_active_idx'),
        ),
        migrations.AddIndex(
            model_name='financialinstrument',
            index=models.Index(fields=['symbol'], name='polygon_financial_instrument_symbol_idx'),
        ),
        migrations.AddIndex(
            model_name='financialinstrument',
            index=models.Index(fields=['instrument_type'], name='polygon_financial_instrument_type_idx'),
        ),
        migrations.AddIndex(
            model_name='marketdatacache',
            index=models.Index(fields=['cache_key'], name='polygon_market_data_cache_key_idx'),
        ),
        migrations.AddIndex(
            model_name='marketdatacache',
            index=models.Index(fields=['expires_at'], name='polygon_market_data_cache_expires_idx'),
        ),
        migrations.AddIndex(
            model_name='stockdata',
            index=models.Index(fields=['instrument', 'timestamp'], name='polygon_stock_data_instrument_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='stockdata',
            index=models.Index(fields=['timestamp'], name='polygon_stock_data_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='optiondata',
            index=models.Index(fields=['underlying_instrument', 'expiration_date'], name='polygon_option_data_underlying_exp_idx'),
        ),
        migrations.AddIndex(
            model_name='optiondata',
            index=models.Index(fields=['option_symbol'], name='polygon_option_data_symbol_idx'),
        ),
        migrations.AddIndex(
            model_name='optiondata',
            index=models.Index(fields=['timestamp'], name='polygon_option_data_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='forexdata',
            index=models.Index(fields=['instrument', 'timestamp'], name='polygon_forex_data_instrument_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='forexdata',
            index=models.Index(fields=['timestamp'], name='polygon_forex_data_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='cryptodata',
            index=models.Index(fields=['instrument', 'timestamp'], name='polygon_crypto_data_instrument_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='cryptodata',
            index=models.Index(fields=['timestamp'], name='polygon_crypto_data_timestamp_idx'),
        ),
        # Add unique constraints
        migrations.AlterUniqueTogether(
            name='stockdata',
            unique_together={('instrument', 'timestamp')},
        ),
        migrations.AlterUniqueTogether(
            name='forexdata',
            unique_together={('instrument', 'timestamp')},
        ),
        migrations.AlterUniqueTogether(
            name='cryptodata',
            unique_together={('instrument', 'timestamp')},
        ),
    ]
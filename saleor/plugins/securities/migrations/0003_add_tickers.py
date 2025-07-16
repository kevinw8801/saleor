# Generated manually for securities plugin - Add Tickers model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('securities', '0002_add_security_daily_prices'),
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
        migrations.AddIndex(
            model_name='tickers',
            index=models.Index(fields=['ticker', 'name'], name='idx_ticker_search'),
        ),
        migrations.AddIndex(
            model_name='tickers',
            index=models.Index(fields=['type'], name='tickers_type_idx'),
        ),
        migrations.AddIndex(
            model_name='tickers',
            index=models.Index(fields=['exchange'], name='tickers_exchange_idx'),
        ),
        migrations.AddIndex(
            model_name='tickers',
            index=models.Index(fields=['active'], name='tickers_active_idx'),
        ),
    ]
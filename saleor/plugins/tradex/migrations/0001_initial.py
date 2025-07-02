# Generated manually for tradex plugin

import decimal
from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Operation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_time', models.DateTimeField(help_text='Date and time when the operation occurred')),
                ('operation', models.CharField(help_text='Type of operation (e.g., buy, sell, dividend, split)', max_length=100)),
                ('equity_id', models.CharField(help_text='Equity identifier (ticker symbol, ISIN, etc.)', max_length=50)),
                ('equity_name', models.CharField(help_text='Human-readable name of the equity', max_length=255)),
                ('market', models.CharField(help_text='Market or exchange where the operation took place', max_length=100)),
                ('amount', models.DecimalField(decimal_places=6, help_text='Amount or quantity of the operation (non-negative)', max_digits=15, validators=[MinValueValidator(decimal.Decimal('0'))])),
                ('fee', models.DecimalField(decimal_places=4, help_text='Fee charged for the operation (non-negative)', max_digits=12, validators=[MinValueValidator(decimal.Decimal('0'))])),
                ('currency', models.CharField(help_text='Currency code (ISO 4217 format, e.g., USD, EUR)', max_length=3)),
                ('price', models.DecimalField(decimal_places=6, help_text='Price per unit (non-negative)', max_digits=15, validators=[MinValueValidator(decimal.Decimal('0'))])),
                ('status', models.CharField(help_text='Status of the operation (e.g., completed, pending, failed)', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Trading Operation',
                'verbose_name_plural': 'Trading Operations',
                'db_table': 'tradex_operation',
                'ordering': ['-date_time', '-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='operation',
            index=models.Index(fields=['equity_id'], name='tradex_oper_equity__6e0a7a_idx'),
        ),
        migrations.AddIndex(
            model_name='operation',
            index=models.Index(fields=['date_time'], name='tradex_oper_date_ti_2fa0d0_idx'),
        ),
        migrations.AddIndex(
            model_name='operation',
            index=models.Index(fields=['operation'], name='tradex_oper_operati_de3c98_idx'),
        ),
        migrations.AddIndex(
            model_name='operation',
            index=models.Index(fields=['status'], name='tradex_oper_status_8a5e1d_idx'),
        ),
        migrations.AddIndex(
            model_name='operation',
            index=models.Index(fields=['market'], name='tradex_oper_market_7c8e2a_idx'),
        ),
    ]
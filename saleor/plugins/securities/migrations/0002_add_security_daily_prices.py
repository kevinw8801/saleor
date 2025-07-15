# Generated manually for securities plugin - Add SecurityDailyPrices model

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('securities', '0001_initial'),
    ]

    operations = [
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
                ('security', models.ForeignKey(help_text='Reference to the security', on_delete=django.db.models.deletion.CASCADE, related_name='daily_prices', to='securities.securities')),
            ],
            options={
                'verbose_name': 'Security Daily Price',
                'verbose_name_plural': 'Security Daily Prices',
                'db_table': 'security_daily_prices',
                'ordering': ['-date', 'security__symbol'],
            },
        ),
        migrations.AddIndex(
            model_name='securitydailyprices',
            index=models.Index(fields=['security', 'date'], name='security_daily_prices_security_date_idx'),
        ),
        migrations.AddIndex(
            model_name='securitydailyprices',
            index=models.Index(fields=['date'], name='security_daily_prices_date_idx'),
        ),
        migrations.AddIndex(
            model_name='securitydailyprices',
            index=models.Index(fields=['security', '-date'], name='security_daily_prices_security_date_desc_idx'),
        ),
        migrations.AddIndex(
            model_name='securitydailyprices',
            index=models.Index(fields=['volume'], name='security_daily_prices_volume_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='securitydailyprices',
            unique_together={('security', 'date')},
        ),
    ]
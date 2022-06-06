# Generated by Django 4.0.4 on 2022-05-28 12:47

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('dataSet', '0011_remove_product_description_product_rate'),
    ]

    operations = [
        migrations.CreateModel(
            name='IncomingInvoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction', models.CharField(max_length=250)),
                ('customer', models.CharField(max_length=250)),
                ('total', models.FloatField(default=0)),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('date_updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='IncomingInvoice_Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('buy_price', models.FloatField(default=0)),
                ('price', models.FloatField(default=0)),
                ('quantity', models.FloatField(default=0)),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dataSet.invoice')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dataSet.product')),
                ('stock', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='dataSet.stock')),
            ],
        ),
    ]

# Generated by Django 4.0.4 on 2022-05-28 09:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataSet', '0005_product_brand_product_unit'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='rate',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
    ]

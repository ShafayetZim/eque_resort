# Generated by Django 4.0.4 on 2022-05-28 11:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dataSet', '0008_remove_product_description_alter_product_category'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='category',
        ),
    ]

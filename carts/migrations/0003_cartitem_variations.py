# Generated by Django 3.2.5 on 2021-07-11 07:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0003_variationmanager'),
        ('carts', '0002_alter_cart_cart_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartitem',
            name='variations',
            field=models.ManyToManyField(blank=True, to='store.Variation'),
        ),
    ]

# Generated by Django 4.0.3 on 2022-04-27 05:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0026_alter_blockchaintransaction_from_address_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='blockchaintransaction',
            name='addresses_involved',
            field=models.ManyToManyField(related_name='transactions_involving', to='database.blockchainaddress'),
        ),
    ]
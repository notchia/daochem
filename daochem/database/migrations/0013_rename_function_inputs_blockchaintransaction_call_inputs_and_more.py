# Generated by Django 4.0.3 on 2022-04-24 20:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0012_alter_blockchaintransactiontrace_table'),
    ]

    operations = [
        migrations.RenameField(
            model_name='blockchaintransaction',
            old_name='function_inputs',
            new_name='call_inputs',
        ),
        migrations.RenameField(
            model_name='blockchaintransaction',
            old_name='function_name',
            new_name='call_name',
        ),
        migrations.RenameField(
            model_name='blockchaintransaction',
            old_name='function_outpus',
            new_name='call_outputs',
        ),
        migrations.RenameField(
            model_name='blockchaintransactiontrace',
            old_name='output',
            new_name='outputs',
        ),
        migrations.RemoveField(
            model_name='blockchaintransaction',
            name='articulated_trace',
        ),
        migrations.RemoveField(
            model_name='blockchaintransactiontrace',
            name='delegates',
        ),
        migrations.AddField(
            model_name='blockchaintransactiontrace',
            name='delegate',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='delegate_for_trace', to='database.blockchainaddress'),
        ),
        migrations.CreateModel(
            name='BlockchainTransactionLog',
            fields=[
                ('id', models.CharField(default='0.0.0', max_length=50, primary_key=True, serialize=False)),
                ('topics', models.CharField(max_length=267, null=True)),
                ('event', models.CharField(max_length=200, null=True)),
                ('compressed_log', models.CharField(max_length=1000, null=True)),
                ('address', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs_from', to='database.blockchainaddress')),
            ],
            options={
                'db_table': 'blockchain_logs',
            },
        ),
        migrations.AddField(
            model_name='blockchaintransaction',
            name='logs',
            field=models.ManyToManyField(related_name='originating_from_transaction', to='database.blockchaintransactionlog'),
        ),
    ]

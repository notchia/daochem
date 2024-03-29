# Generated by Django 4.0.3 on 2022-09-08 04:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0030_deepdaocategory_deepdaodao_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deepdaoaddressdeprecated',
            name='address',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='deepdao_info_deprecated', to='database.blockchainaddress'),
        ),
        migrations.CreateModel(
            name='DeepdaoAddress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('address', models.CharField(max_length=100)),
                ('platform', models.CharField(choices=[('', 'Not specified'), ('ARAGON', 'Aragon'), ('COLONY', 'Colony'), ('COMPOUND', 'Compound'), ('DAOHAUS', 'DAOhaus'), ('DAOSTACK', 'DAOstack'), ('INDEPENDENT', 'Independent'), ('OPENLAW', 'OpenLaw'), ('REALMS', 'Realms'), ('SAFE', 'Safe'), ('SNAPSHOT', 'Snapshot')], default='', max_length=11)),
                ('deepdao_id', models.CharField(max_length=36, unique=True)),
                ('blockchain_address', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='deepdao_info', to='database.blockchainaddress')),
                ('deepdao_record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deepdao_info', to='database.deepdaodao')),
            ],
            options={
                'db_table': 'deepdao_addresses',
                'unique_together': {('address', 'platform')},
            },
        ),
    ]

# Generated by Django 4.0.3 on 2022-04-21 03:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0004_rename_metrics_impression_count_tweet_like_count_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='tweet',
            name='urls',
            field=models.CharField(default='', max_length=200),
        ),
    ]

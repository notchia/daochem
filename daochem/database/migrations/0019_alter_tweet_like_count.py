# Generated by Django 4.0.3 on 2022-04-26 02:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0018_alter_tweet_urls'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tweet',
            name='like_count',
            field=models.PositiveIntegerField(),
        ),
    ]
# Generated by Django 5.2 on 2025-04-23 19:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_message'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='preferred_age_max',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='preferred_age_min',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='preferred_gender',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]

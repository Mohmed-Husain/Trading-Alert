# Generated by Django 5.1.6 on 2025-04-14 06:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0006_usernotificationpreferences'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usernotificationpreferences',
            name='alert_types',
        ),
        migrations.RemoveField(
            model_name='usernotificationpreferences',
            name='email_address',
        ),
        migrations.RemoveField(
            model_name='usernotificationpreferences',
            name='notify_on_bollinger',
        ),
        migrations.RemoveField(
            model_name='usernotificationpreferences',
            name='notify_on_macd',
        ),
        migrations.RemoveField(
            model_name='usernotificationpreferences',
            name='notify_on_moving_avg',
        ),
        migrations.RemoveField(
            model_name='usernotificationpreferences',
            name='notify_on_rsi',
        ),
    ]

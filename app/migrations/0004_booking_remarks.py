# Generated by Django 4.0.5 on 2022-10-13 13:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_booking'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='remarks',
            field=models.TextField(blank=True, default='', verbose_name='備考'),
        ),
    ]
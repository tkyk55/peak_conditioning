# Generated by Django 4.0.5 on 2024-12-02 13:50

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('app_staff', '0009_alter_closingday_training_no'),
    ]

    operations = [
        migrations.AddField(
            model_name='staffwork',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='作成時間'),
        ),
        migrations.AddField(
            model_name='staffwork',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='更新時間'),
        ),
    ]

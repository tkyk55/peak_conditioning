# Generated by Django 4.0.5 on 2022-11-19 06:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_delete_master'),
    ]

    operations = [
        migrations.CreateModel(
            name='Master',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(max_length=30, verbose_name='カテゴリ')),
                ('set_value', models.CharField(max_length=30, verbose_name='設定値')),
            ],
        ),
    ]
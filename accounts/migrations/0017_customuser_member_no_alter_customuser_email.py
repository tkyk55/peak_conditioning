# Generated by Django 4.0.5 on 2023-05-29 13:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0016_remove_customuser_end_end_customuser_end_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='member_no',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='会員番号'),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='email',
            field=models.EmailField(default='', max_length=254, unique=True, verbose_name='メールアドレス'),
        ),
    ]

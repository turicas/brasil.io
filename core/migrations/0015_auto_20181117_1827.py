# Generated by Django 2.1.3 on 2018-11-17 18:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_auto_20180908_1902'),
    ]

    operations = [
        migrations.AlterField(
            model_name='field',
            name='frontend_filter',
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AlterField(
            model_name='field',
            name='has_choices',
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AlterField(
            model_name='field',
            name='null',
            field=models.BooleanField(blank=True, default=True),
        ),
        migrations.AlterField(
            model_name='field',
            name='obfuscate',
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AlterField(
            model_name='field',
            name='show',
            field=models.BooleanField(blank=True, default=True),
        ),
        migrations.AlterField(
            model_name='field',
            name='show_on_frontend',
            field=models.BooleanField(blank=True, default=False),
        ),
    ]

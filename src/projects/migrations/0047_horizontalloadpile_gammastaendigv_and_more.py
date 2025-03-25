# Generated by Django 5.1 on 2025-01-08 04:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0046_alter_horizontalloadpile_hgkx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='horizontalloadpile',
            name='gammaStaendigV',
            field=models.FloatField(blank=True, default=0, null=True, verbose_name='gammaStaendigV'),
        ),
        migrations.AddField(
            model_name='horizontalloadpile',
            name='gammaVeraenderlichV',
            field=models.FloatField(blank=True, default=0, null=True, verbose_name='gammaVeraenderlichV'),
        ),
    ]

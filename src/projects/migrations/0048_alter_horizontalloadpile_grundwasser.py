# Generated by Django 5.1 on 2025-01-08 05:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0047_horizontalloadpile_gammastaendigv_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='horizontalloadpile',
            name='Grundwasser',
            field=models.FloatField(default=0, null=True, verbose_name='Grundwasser'),
        ),
    ]

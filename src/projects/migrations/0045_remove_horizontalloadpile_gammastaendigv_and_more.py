# Generated by Django 5.1 on 2025-01-08 03:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0044_alter_horizontalloadpile_grundwasser_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='horizontalloadpile',
            name='gammaStaendigV',
        ),
        migrations.RemoveField(
            model_name='horizontalloadpile',
            name='gammaVeraenderlichV',
        ),
    ]

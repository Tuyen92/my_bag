# Generated by Django 5.1 on 2025-02-06 04:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0059_alter_projectsettings_nameanlageauszen'),
    ]

    operations = [
        migrations.AddField(
            model_name='horizontalloadpile',
            name='pAnOberkante',
            field=models.FloatField(default=0, verbose_name='pAnOberkante'),
        ),
    ]

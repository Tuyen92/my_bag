# Generated by Django 5.1 on 2024-12-26 08:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0013_projectsettings_runhorbemessung'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pile',
            name='PfahlTyp',
            field=models.CharField(blank=True, max_length=16, verbose_name='PfahlTyp'),
        ),
    ]

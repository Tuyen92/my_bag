# Generated by Django 5.1 on 2025-02-05 10:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0058_alter_project_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projectsettings',
            name='nameAnlageAuszen',
            field=models.CharField(blank=True, default='', null=True, verbose_name='nameAnlageAuszen'),
        ),
    ]

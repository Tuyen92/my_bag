# Generated by Django 5.1 on 2024-12-26 13:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0016_rename_pfahltyp_soilprofile_pfahltyp'),
    ]

    operations = [
        migrations.AddField(
            model_name='soillayer',
            name='MaxElementWeite',
            field=models.FloatField(blank=True, default=0, verbose_name='MaxElementWeite'),
        ),
    ]

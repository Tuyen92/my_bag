# Generated by Django 5.1 on 2025-01-08 11:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0049_projectsettings_langsbewehrungbugelbewehrung_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='pile',
            name='AlternativeCharakteristischeMinLastZ',
            field=models.FloatField(default=0, verbose_name='AlternativeCharakteristischeMinLastZ'),
        ),
        migrations.AddField(
            model_name='pile',
            name='AlternativeDesignMinLastZ',
            field=models.FloatField(default=0, verbose_name='AlternativeDesignMinLastZ'),
        ),
    ]

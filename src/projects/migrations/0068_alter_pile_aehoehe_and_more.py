# Generated by Django 5.1 on 2025-02-18 09:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0067_alter_projectsettings_schrittweite'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pile',
            name='AEHoehe',
            field=models.FloatField(null=True, verbose_name='Drilling level'),
        ),
        migrations.AlterField(
            model_name='pile',
            name='AlternativeCharakteristischeLastZ',
            field=models.FloatField(null=True, verbose_name='AlternativeCharakteristischeLastZ'),
        ),
        migrations.AlterField(
            model_name='pile',
            name='AlternativeCharakteristischeMinLastZ',
            field=models.FloatField(default=0, null=True, verbose_name='AlternativeCharakteristischeMinLastZ'),
        ),
        migrations.AlterField(
            model_name='pile',
            name='AlternativeDesignLastZ',
            field=models.FloatField(null=True, verbose_name='AlternativeDesignLastZ'),
        ),
        migrations.AlterField(
            model_name='pile',
            name='AlternativeDesignMinLastZ',
            field=models.FloatField(default=0, null=True, verbose_name='AlternativeDesignMinLastZ'),
        ),
        migrations.AlterField(
            model_name='pile',
            name='BetonZyl',
            field=models.IntegerField(blank=True, default=25, null=True, verbose_name='BetonZyl'),
        ),
        migrations.AlterField(
            model_name='pile',
            name='BodenProfil',
            field=models.CharField(max_length=64, null=True, verbose_name='Soil Profile'),
        ),
        migrations.AlterField(
            model_name='pile',
            name='Hochwert',
            field=models.FloatField(null=True, verbose_name='Hochwert'),
        ),
        migrations.AlterField(
            model_name='pile',
            name='Pname',
            field=models.CharField(help_text='Unique load point name for this project', max_length=64, null=True, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='pile',
            name='Rechtswert',
            field=models.FloatField(null=True, verbose_name='Rechtswert'),
        ),
        migrations.AlterField(
            model_name='pile',
            name='SollDurchmesser',
            field=models.FloatField(null=True, verbose_name='SollDurchmesser'),
        ),
        migrations.AlterField(
            model_name='pile',
            name='SollPfahlOberKante',
            field=models.FloatField(null=True, verbose_name='SollPfahlOberKante'),
        ),
    ]

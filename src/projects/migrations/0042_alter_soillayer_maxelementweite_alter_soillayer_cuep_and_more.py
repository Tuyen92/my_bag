# Generated by Django 5.1 on 2025-01-03 07:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0041_alter_horizontalloadpile_aslaengs_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='soillayer',
            name='MaxElementWeite',
            field=models.FloatField(blank=True, default=0, null=True, verbose_name='MaxElementWeite'),
        ),
        migrations.AlterField(
            model_name='soillayer',
            name='cuEP',
            field=models.FloatField(blank=True, null=True, verbose_name='cuEP'),
        ),
        migrations.AlterField(
            model_name='soillayer',
            name='cuk',
            field=models.FloatField(blank=True, null=True, verbose_name='cuk'),
        ),
        migrations.AlterField(
            model_name='soillayer',
            name='deltaVonPhi',
            field=models.FloatField(blank=True, null=True, verbose_name='deltaVonPhi'),
        ),
        migrations.AlterField(
            model_name='soillayer',
            name='qbk002',
            field=models.FloatField(blank=True, null=True, verbose_name='qbk002'),
        ),
        migrations.AlterField(
            model_name='soillayer',
            name='qbk003',
            field=models.FloatField(blank=True, null=True, verbose_name='qbk003'),
        ),
        migrations.AlterField(
            model_name='soillayer',
            name='qbk01',
            field=models.FloatField(blank=True, null=True, verbose_name='qbk01'),
        ),
        migrations.AlterField(
            model_name='soillayer',
            name='qsk',
            field=models.FloatField(blank=True, null=True, verbose_name='qsk'),
        ),
    ]

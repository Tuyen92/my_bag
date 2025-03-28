# Generated by Django 5.1 on 2025-02-04 08:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0055_alter_horizontalloadpile_options_alter_pile_options_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='projectsettings',
            name='LangsbewehrungBugelbewehrung',
        ),
        migrations.RemoveField(
            model_name='projectsettings',
            name='MmaxSchubbemessung',
        ),
        migrations.RemoveField(
            model_name='projectsettings',
            name='einzelMaximaleBohrtiefe',
        ),
        migrations.RemoveField(
            model_name='projectsettings',
            name='mantelreibungcu',
        ),
        migrations.RemoveField(
            model_name='projectsettings',
            name='mantelreibungqc',
        ),
        migrations.RemoveField(
            model_name='projectsettings',
            name='maxBugelbewehrung',
        ),
        migrations.RemoveField(
            model_name='projectsettings',
            name='maxLangsbewehrung',
        ),
        migrations.RemoveField(
            model_name='projectsettings',
            name='reinforcingSteel',
        ),
        migrations.RemoveField(
            model_name='projectsettings',
            name='selectedConcreteCover',
        ),
        migrations.RemoveField(
            model_name='projectsettings',
            name='spritzendruckcu',
        ),
        migrations.RemoveField(
            model_name='projectsettings',
            name='spritzendruckqc',
        ),
        migrations.AddField(
            model_name='projectsettings',
            name='Betondeckung',
            field=models.FloatField(default=0.12, verbose_name='Betondeckung'),
        ),
        migrations.AddField(
            model_name='projectsettings',
            name='MaxBuegel',
            field=models.FloatField(default=0.008, verbose_name='MaxBuegel'),
        ),
        migrations.AddField(
            model_name='projectsettings',
            name='MaxLaengs',
            field=models.FloatField(default=0.016, verbose_name='MaxLaengs'),
        ),
        migrations.AddField(
            model_name='projectsettings',
            name='MinLaengsAbstand',
            field=models.FloatField(default=0.1, verbose_name='MinLaengsAbstand'),
        ),
        migrations.AddField(
            model_name='projectsettings',
            name='MvonMaxfuerSchub',
            field=models.FloatField(default=0.5, verbose_name='MvonMaxfuerSchub'),
        ),
        migrations.AddField(
            model_name='projectsettings',
            name='Stahlsorte',
            field=models.CharField(default='B500B', verbose_name='Stahlsorte'),
        ),
        migrations.AddField(
            model_name='projectsettings',
            name='qbkCukAb0',
            field=models.BooleanField(default=False, verbose_name='qbkCukAb0'),
        ),
        migrations.AddField(
            model_name='projectsettings',
            name='qbkQcAb0',
            field=models.BooleanField(default=False, verbose_name='qbkQcAb0'),
        ),
        migrations.AddField(
            model_name='projectsettings',
            name='qskCukAb0',
            field=models.BooleanField(default=False, verbose_name='qskCukAb0'),
        ),
        migrations.AddField(
            model_name='projectsettings',
            name='qskQcAb0',
            field=models.BooleanField(default=False, verbose_name='qskQcAb0'),
        ),
        migrations.AlterField(
            model_name='projectsettings',
            name='falsermInner',
            field=models.IntegerField(default=1, verbose_name='falsermInner'),
        ),
    ]

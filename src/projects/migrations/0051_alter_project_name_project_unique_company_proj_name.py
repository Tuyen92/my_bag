# Generated by Django 5.1 on 2025-01-10 04:08

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0004_company_is_active'),
        ('projects', '0050_pile_alternativecharakteristischeminlastz_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='name',
            field=models.CharField(help_text='The name of the project.', max_length=255, verbose_name='Project Name'),
        ),
        migrations.AddConstraint(
            model_name='project',
            constraint=models.UniqueConstraint(fields=('company', 'name'), name='unique_company_proj_name'),
        ),
    ]

# Generated by Django 5.1 on 2025-02-13 08:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0065_projectsettings_default_company_info'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectsettings',
            name='companyAltLogo',
            field=models.CharField(blank=True, default='', max_length=128, null=True, verbose_name='companyAltLogo'),
        ),
    ]

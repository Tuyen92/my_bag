# Generated by Django 5.1 on 2024-12-20 08:29

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0002_company_address_company_created_by_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='created_date',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False),
        ),
    ]

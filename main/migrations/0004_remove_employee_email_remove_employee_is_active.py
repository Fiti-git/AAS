# Generated by Django 5.2 on 2025-04-04 14:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_rename_agency_employee_outlet'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='employee',
            name='email',
        ),
        migrations.RemoveField(
            model_name='employee',
            name='is_active',
        ),
    ]

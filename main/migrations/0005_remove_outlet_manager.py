# Generated by Django 5.2 on 2025-04-04 14:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_remove_employee_email_remove_employee_is_active'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='outlet',
            name='manager',
        ),
    ]

# Generated by Django 5.2 on 2025-04-03 11:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_remove_agency_manager'),
    ]

    operations = [
        migrations.RenameField(
            model_name='employee',
            old_name='agency',
            new_name='outlet',
        ),
    ]

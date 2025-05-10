#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from django.core.management import execute_from_command_line
from django.core.management import call_command
from django.contrib.auth import get_user_model


def create_superuser():
    """Create superuser if one doesn't exist."""
    User = get_user_model()
    username = 'admin'
    password = 'adminpassword'
    email = 'admin@example.com'

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, password=password, email=email)
        print("Superuser created successfully!")
    else:
        print("Superuser already exists.")


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aas.settings')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Call the function to create the superuser
    create_superuser()

    # Execute the Django management command (e.g., runserver, migrate, etc.)
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

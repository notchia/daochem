import sys

if not(sys.argv[0].endswith('manage.py')):
    import os
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "daochem.settings")
    django.setup()
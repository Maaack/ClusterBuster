import os

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):

    def handle(self, *args, **options):
        if "DJANGO_SUPERUSER_USERNAME" in os.environ:
            username = os.environ["DJANGO_SUPERUSER_USERNAME"]
            email = os.environ["DJANGO_SUPERUSER_EMAIL"]
            password = os.environ["DJANGO_SUPERUSER_PASSWORD"]
            if not User.objects.filter(username=username).exists():
                User.objects.create_superuser(username, email, password)

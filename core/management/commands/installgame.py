import os

from django.core.management.base import BaseCommand

from ...models import ClusterBuster


class Command(BaseCommand):
    def handle(self, *args, **options):
        ClusterBuster.install_game()

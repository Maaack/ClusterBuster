from django.db import models


class ActiveLobbyManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(session=None)


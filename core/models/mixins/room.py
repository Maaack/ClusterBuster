from django.db import models


class GamesRoom(models.Model):
    class Meta:
        abstract = True

    current_game = models.ForeignKey('Game', on_delete=models.SET_NULL, related_name="+", null=True, blank=True)


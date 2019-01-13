from django.db import models


class RoundsGame(models.Model):
    class Meta:
        abstract = True

    current_round = models.ForeignKey('Round', on_delete=models.SET_NULL, related_name="+", null=True, blank=True)


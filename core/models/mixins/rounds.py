from django.db import models


class RoundsGame(models.Model):
    class Meta:
        abstract = True

    current_round = models.ForeignKey('Round', on_delete=models.SET_NULL, related_name="+", null=True, blank=True)


class RoundsParty(models.Model):
    class Meta:
        abstract = True

    current_party_round = models.ForeignKey('PartyRound', on_delete=models.SET_NULL, related_name="+", null=True,
                                            blank=True)

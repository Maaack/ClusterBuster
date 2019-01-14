from django.db import models
from django.utils.translation import ugettext_lazy as _

from core.models import choices


class StagesRound(models.Model):
    class Meta:
        abstract = True

    stage = models.PositiveSmallIntegerField(_("Stage"), default=choices.RoundStages.COMPOSING.value,
                                             choices=choices.RoundStages.choices())


class StagesPartyRound(models.Model):
    class Meta:
        abstract = True

    stage = models.PositiveSmallIntegerField(_("Stage"), default=choices.TeamRoundStages.ACTIVE.value,
                                             choices=choices.TeamRoundStages.choices())
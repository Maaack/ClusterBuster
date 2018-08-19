from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.sessions.models import Session
from clusterbuster.mixins import ChoiceEnum


class SessionRequired(models.Model):
    class Meta:
        abstract = True

    session = models.ForeignKey(Session, on_delete=models.CASCADE, verbose_name=_("Session"))


class SessionOptional(models.Model):
    class Meta:
        abstract = True

    session = models.ForeignKey(Session, on_delete=models.SET_NULL, verbose_name=_("Session"), null=True, blank=True)


class GameRoomStages(ChoiceEnum):
    CLOSED = 0
    OPEN = 1
    PLAYING = 2
    PAUSED = 3
    DONE = 4


class RoundStages(ChoiceEnum):
    COMPOSING = 0
    REVEALING = 1
    GUESSING = 2
    SCORING = 3
    DONE = 4


class TeamRoundStages(ChoiceEnum):
    ACTIVE = 0
    INACTIVE = 1
    WAITING = 2
    DONE = 3

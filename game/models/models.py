from django.db import models
from django.utils.translation import ugettext_lazy as _

from clusterbuster.mixins import TimeStamped

from rooms.models import Player, Team, Room


class LeafState(TimeStamped):
    """
    State with a label.
    """
    label = models.SlugField(_("Label"), max_length=32)

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.label)


class State(LeafState):
    """
    State with links to other states.
    """
    parent_state = models.ForeignKey('State', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = _("State")
        verbose_name_plural = _("States")

    def __str__(self):
        return str(self.label)


class Stage(State):
    """
    Stages are named and typically distinct from their neighbors.
    """
    name = models.CharField(_("Name"), max_length=64)

    class Meta:
        verbose_name = _("Stage")
        verbose_name_plural = _("Stages")

    def __str__(self):
        return str(self.name)


class Round(State):
    """
    Rounds are sequentially numbered and typically similar to their neighbors.
    """
    number = models.PositiveSmallIntegerField(_("Number"))

    class Meta:
        verbose_name = _("Stage")
        verbose_name_plural = _("Stages")

    def __str__(self):
        return "Round " + str(self.number)


class ConsecutiveTeamTurn(State):
    """
    Turns to all teams simultaneously.
    """
    teams = models.ManyToManyField(Team, blank=True)


class ConsecutivePlayerTurn(State):
    """
    Turns to all players simultaneously.
    """
    players = models.ManyToManyField(Player, blank=True)


class SequentialTurn(State):
    """
    Turns are sequentially numbered and applied to a player or team.
    """
    turn = models.PositiveSmallIntegerField(_("Turn"))


class SequentialTeamTurn(SequentialTurn):
    """
    Turns for each team, one at a time.
    """
    team = models.ForeignKey(Team)


class SequentialPlayerTurn(SequentialTurn):
    """
    Turns for each team, one at a time.
    """
    player = models.ForeignKey(Player)

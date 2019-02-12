from django.db import models
from django.utils.translation import ugettext_lazy as _

from clusterbuster.mixins import TimeStamped
from core.basics.utils import CodeGenerator

from rooms.models import Player, Team, Room


class Parameter(TimeStamped):
    """
    Condition with a label and condition method.
    """
    key = models.SlugField(_("Key"), max_length=32)
    value = models.BooleanField(_("Value"), default=False)

    def __str__(self):
        return str(self.key) + ": " + str(self.value)


class Condition(TimeStamped):
    """
    Condition wraps a parameter.
    """
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.parameter)

    def passes(self):
        return bool(self.parameter.value)


class BaseState(TimeStamped):
    """
    State with a label.
    """
    label = models.SlugField(_("Label"), max_length=32)

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.label)


class State(BaseState):
    """
    State with links to other states.
    """
    parent_state = models.ForeignKey('State', on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    transitions = models.ManyToManyField('Transition', blank=True, related_name="+")

    class Meta:
        verbose_name = _("State")
        verbose_name_plural = _("States")


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
    teams = models.ManyToManyField(Team, blank=True, related_name="+")


class ConsecutivePlayerTurn(State):
    """
    Turns to all players simultaneously.
    """
    players = models.ManyToManyField(Player, blank=True, related_name="+")


class SequentialTurn(State):
    """
    Turns are sequentially numbered and applied to a player or team.
    """
    turn = models.PositiveSmallIntegerField(_("Turn"))


class SequentialTeamTurn(SequentialTurn):
    """
    Turns for each team, one at a time.
    """
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="+")


class SequentialPlayerTurn(SequentialTurn):
    """
    Turns for each team, one at a time.
    """
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="+")


class Transition(TimeStamped):
    """
    Transition pass Conditions to State.
    """
    to_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="+")
    conditions = models.ManyToManyField(Condition, blank=True, related_name="transitions")

    def __can_transit(self):
        conditions = self.conditions.all()
        for condition in conditions:
            if not condition.passes():
                return False
        return True

    def can_transit(self):
        return self.__can_transit()


class StateMachine(TimeStamped):
    """
    State Machines manage the State and its Transitions.
    """
    current_state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True)
    parameters = models.ManyToManyField(Condition, blank=True)

    def __transition(self):
        if self.current_state.transitions.count() > 0:
            for transition in self.current_state.transitions.all():
                if transition.can_transit():
                    self.current_state = transition.to_state
                    self.save()
                    return

    def transition(self):
        self.__transition()


class Game(StateMachine):
    """
    A simple game with a code, state, players, and teams.
    """
    code = models.SlugField(_("Code"), max_length=16)
    players = models.ManyToManyField(Player, blank=True, related_name='games')
    teams = models.ManyToManyField(Team, blank=True, related_name='games')
    room = models.ForeignKey(Room, null=True, blank=True, on_delete=models.SET_NULL, related_name='games')
    leader = models.ForeignKey(Player, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    class Meta:
        verbose_name = _("Game")
        verbose_name_plural = _("Games")
        ordering = ["-created"]

    def __str__(self):
        return str(self.code)

    def __setup_code(self):
        if not self.code:
            self.code = CodeGenerator.game_code()

    def __setup_from_room(self, room: Room):
        self.room = room
        self.players = room.players
        self.teams = room.teams
        self.save()

    def save(self, *args, **kwargs):
        self.__setup_code()
        super(Game, self).save(*args, **kwargs)

    def has_player(self, player) -> bool:
        """
        Returns `True` if the player is in the game.
        :param player: Player
        :return: bool
        """
        return self.players.filter(pk=player.pk).exists()

    def has_team(self, team) -> bool:
        """
        Returns `True` if the team is in the room.
        :param team: Team
        :return: bool
        """
        return self.teams.filter(pk=team.pk).exists()

    def has(self, model_object) -> bool:
        """
        Returns `True` if the room has the player or team in it.
        :param model_object: Player or Team
        :return:
        """
        if isinstance(model_object, Player):
            return self.has_player(player=model_object)
        elif isinstance(model_object, Team):
            return self.has_team(team=model_object)
        return False

    def setup(self, room: Room):
        """
        Sets up the game from a room.
        :param room: Room
        :return:
        """
        self.__setup_from_room(room)


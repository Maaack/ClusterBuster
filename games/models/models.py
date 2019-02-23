from django.db import models
from django.utils.translation import ugettext_lazy as _

from clusterbuster.mixins import TimeStamped
from core.basics.utils import CodeGenerator

from rooms.models import Player, Team, Room

__all__ = ['Parameter', 'Condition', 'Transition', 'State', 'StateMachine', 'Game']


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


class Payload(TimeStamped):
    """
    Payload links to a State
    """

    class Meta:
        abstract = True


class State(TimeStamped):
    """
    State with label, payload, parent, and transitions to other states.
    """
    label = models.SlugField(_("Label"), max_length=32)
    payload = models.ForeignKey(Payload, on_delete=models.SET_NULL, null=True, blank=True)
    parent_state = models.ForeignKey('State', on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    transitions = models.ManyToManyField('Transition', blank=True, related_name="+")

    class Meta:
        verbose_name = _("State")
        verbose_name_plural = _("States")

    def __str__(self):
        return str(self.label)


class Stage(Payload):
    """
    Stages are named and typically distinct from their neighbors.
    """
    name = models.CharField(_("Name"), max_length=64)

    class Meta:
        verbose_name = _("Stage")
        verbose_name_plural = _("Stages")

    def __str__(self):
        return str(self.name)


class Round(Payload):
    """
    Rounds are sequentially numbered and typically similar to their neighbors.
    """
    number = models.PositiveSmallIntegerField(_("Number"))

    class Meta:
        verbose_name = _("Round")
        verbose_name_plural = _("Rounds")

    def __str__(self):
        return "Round " + str(self.number)


class ConsecutiveTeamTurn(Payload):
    """
    Turns to all teams simultaneously.
    """
    teams = models.ManyToManyField(Team, blank=True, related_name="+")


class ConsecutivePlayerTurn(Payload):
    """
    Turns to all players simultaneously.
    """
    players = models.ManyToManyField(Player, blank=True, related_name="+")


class SequentialTurn(Payload):
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

    def add_parameter(self, parameter):
        condition = Condition.objects.create(parameter=parameter)
        self.conditions.add(condition)


class StateMachine(TimeStamped):
    """
    State Machines manage the State and its Transitions.
    """
    root_state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True)
    current_state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True)
    parameters = models.ManyToManyField(Parameter, blank=True)

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
        self.players.set(room.players.all())
        self.teams.set(room.teams.all())
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


class ClusterBusterGame(Game):
    """
    A game of Cluster Buster!
    """
    code = models.SlugField(_("Code"), max_length=16)
    players = models.ManyToManyField(Player, blank=True, related_name='games')
    teams = models.ManyToManyField(Team, blank=True, related_name='games')
    room = models.ForeignKey(Room, null=True, blank=True, on_delete=models.SET_NULL, related_name='games')
    leader = models.ForeignKey(Player, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    class Meta:
        verbose_name = _("Cluster Buster Game")
        verbose_name_plural = _("Cluster Buster Games")
        ordering = ["-created"]

    def __init_state(self) -> State:
        init_state = State.objects.create(label="init_cluster_buster")
        self.current_state = init_state
        self.save()
        return init_state

    def __setup_game_state(self, state: State) -> State:
        game_state = State.objects.create(label="ready_cluster_buster")
        transition = Transition.objects.create(to_state=game_state)
        parameter = Parameter.objects.create(key="game_setup", value=False)
        self.parameters.add(parameter)
        transition.add_parameter(parameter)
        state.transitions.add(transition)
        state.save()
        return game_state

    def __setup_cluster_buster(self):
        init_state = self.__init_state()
        self.__setup_game_state(init_state)

    def setup(self, room: Room):
        """
        Sets up the game from a room.
        :param room: Room
        :return:
        """
        super(ClusterBusterGame, self).setup(room)
        self.__setup_cluster_buster()

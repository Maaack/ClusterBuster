from itertools import chain

from django.db import models
from django.utils.translation import ugettext_lazy as _

from clusterbuster.mixins import TimeStamped
from core.basics.utils import CodeGenerator

from rooms.models import Player, Team, Room
from .constants import GameStates


class State(TimeStamped):
    """
    States determine the rules that currently apply to the Game.
    """
    label = models.SlugField(_("Label"), max_length=32)

    class Meta:
        verbose_name = _("State")
        verbose_name_plural = _("States")

    def __str__(self):
        return str(self.label)


class Transition(TimeStamped):
    """
    Transitions define how the StateMachine can move from one State to another State.
    """
    label = models.SlugField(_("Label"), max_length=32)
    from_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="transitions_out")
    to_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="transitions_in")


class Parameter(TimeStamped):
    """
    Parameters store all data about a specific game and the state.
    """
    key = models.SlugField(_("Key"), max_length=32)

    def __str__(self):
        return str(self.key)


class BooleanParameter(Parameter):
    """
    Value stores True/False
    """
    value = models.BooleanField(_("Value"), default=False)

    def __str__(self):
        return str(self.key) + ": " + str(self.value)


class IntegerParameter(Parameter):
    """
    Value stores ...-2, -1, 0, 1, 2...
    """
    value = models.IntegerField(_("Value"), default=0)

    def __str__(self):
        return str(self.key) + ": " + str(self.value)


class Condition(TimeStamped):
    """
    Condition wraps a parameter.
    """
    transition = models.ForeignKey(Transition, on_delete=models.CASCADE, related_name="+")

    class Meta:
        abstract = True

    def passes(self):
        return False

    def get_next_state(self):
        return self.transition.to_state


class BooleanCondition(Condition):
    parameter = models.ForeignKey(BooleanParameter, on_delete=models.CASCADE, related_name="+")

    def __str__(self):
        return str(self.parameter)

    def passes(self):
        return bool(self.parameter.value)


class IntegerCondition(Condition):
    NOT_EQUAL = 0
    EQUAL = 1
    GREATER_THAN = 2
    LESS_THAN = 3
    GREATER_THAN_OR_EQUAL = 4
    LESS_THAN_OR_EQUAL = 4
    COMPARISON_OPTIONS = (
        (NOT_EQUAL, "!="),
        (EQUAL, "=="),
        (GREATER_THAN, ">"),
        (LESS_THAN, "<"),
        (GREATER_THAN_OR_EQUAL, ">="),
        (LESS_THAN_OR_EQUAL, "<="),
    )

    comparison = models.PositiveSmallIntegerField(_("Comparison Operation"), choices=COMPARISON_OPTIONS)

    class Meta:
        abstract = True

    def __is_not_equal(self):
        return self.comparison == IntegerCondition.NOT_EQUAL

    def __is_equal(self):
        return self.comparison == IntegerCondition.EQUAL

    def __is_gt(self):
        return self.comparison == IntegerCondition.GREATER_THAN

    def __is_lt(self):
        return self.comparison == IntegerCondition.LESS_THAN

    def __is_gt_or_equal(self):
        return self.comparison == IntegerCondition.GREATER_THAN_OR_EQUAL

    def __is_lt_or_equal(self):
        return self.comparison == IntegerCondition.LESS_THAN_OR_EQUAL

    def __compare_2_ints(self, integer_1, integer_2):
        if self.__is_not_equal():
            return integer_1 != integer_2
        if self.__is_equal():
            return integer_1 == integer_2
        if self.__is_gt():
            return integer_1 > integer_2
        if self.__is_lt():
            return integer_1 < integer_2
        if self.__is_gt_or_equal():
            return integer_1 >= integer_2
        if self.__is_lt_or_equal():
            return integer_1 <= integer_2

    def get_readable_comparison(self):
        return self.get_comparison_display()


class FixedIntegerCondition(IntegerCondition):
    parameter = models.ForeignKey(IntegerParameter, on_delete=models.CASCADE, related_name="+")
    integer = models.IntegerField(_("Integer"))

    def __str__(self):
        return str(self.parameter)

    def passes(self):
        return self.__compare_2_ints(self.parameter.value, self.integer)


class VariableIntegerCondition(IntegerCondition):
    parameter_1 = models.ForeignKey(IntegerParameter, on_delete=models.CASCADE, related_name="+")
    parameter_2 = models.ForeignKey(IntegerParameter, on_delete=models.CASCADE, related_name="+")

    def __str__(self):
        comparison_str = self.get_comparison_display()
        return str(self.parameter_1) + comparison_str + str(self.parameter_2)

    def passes(self):
        return self.__compare_2_ints(self.parameter_1.value, self.parameter_2.value)


class StateMachine(TimeStamped):
    """
    State Machines manage the State and its Transitions.
    """
    root_state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    previous_state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    current_state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    parameters = models.ManyToManyField(Parameter, blank=True)
    boolean_conditions = models.ManyToManyField(BooleanCondition, blank=True, related_name="transitions")
    fixed_integer_conditions = models.ManyToManyField(FixedIntegerCondition, blank=True, related_name="transitions")
    variable_integer_conditions = models.ManyToManyField(VariableIntegerCondition, blank=True,
                                                         related_name="transitions")

    def __transit_to_state(self, state: State):
        self.previous_state = self.current_state
        self.current_state = state
        self.save()

    def get_conditions(self):
        return list(chain(self.boolean_conditions.all(),
                          self.fixed_integer_conditions.all(),
                          self.variable_integer_conditions.all()))

    def can_transit(self):
        conditions = self.get_conditions()
        for condition in conditions:
            if condition.passes():
                return True
        return False

    def transition(self):
        conditions = self.get_conditions()
        for condition in conditions:
            if condition.passes():
                next_state = condition.get_next_state()
                self.__transit_to_state(next_state)


class GameDefinition(TimeStamped):

    slug = models.SlugField(_("Slug"), max_length=64)
    title = models.CharField(_("Title"), max_length=128, default='')
    description = models.TextField(_("Description"), default='')
    root_states = models.ManyToManyField(State, blank=True, related_name='+')

    class Meta:
        verbose_name = _("Game Definition")
        verbose_name_plural = _("Games Definitions")
        ordering = ["-created"]

    def __str__(self):
        return str(self.slug)

    def __init__(self, *args, **kwargs):
        super(GameDefinition, self).__init__(*args, **kwargs)
        self.state_rules = []
        self.transition_rules = []


class Game(TimeStamped):
    """
    Games are instances of Game Definitions, that have codes, State Machines, Players, and Teams.
    """
    game_definition = models.ForeignKey(GameDefinition, on_delete=models.SET_NULL, null=True, blank=True)
    state_machines = models.ManyToManyField(StateMachine, blank=True)
    code = models.SlugField(_("Code"), max_length=16)
    players = models.ManyToManyField(Player, blank=True, related_name='games')
    teams = models.ManyToManyField(Team, blank=True, related_name='games')
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='games')
    leader = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    class Meta:
        verbose_name = _("Game")
        verbose_name_plural = _("Games")
        ordering = ["-created"]

    def __str__(self):
        return str(self.code)

    def __setup_code(self):
        if not self.code:
            self.code = CodeGenerator.game_code()

    def __setup_game_defintion(self, game_definition_slug):
        """
        :param game_definition: GameDefinition
        :return:
        """
        self.game_definition = GameDefinition.objects.get(slug=game_definition_slug)

    def __setup_state_machines(self):
        if self.game_definition:
            for root_state in self.game_definition.root_states.all():
                self.state_machines.create(root_state=root_state)
            self.save()

    def __setup_from_room(self, room: Room):
        self.room = room
        self.players.set(room.players.all())
        self.teams.set(room.teams.all())
        self.save()

    def save(self, *args, **kwargs):
        super(Game, self).save(*args, **kwargs)

    def has_player(self, player: Player) -> bool:
        """
        Returns `True` if the player is in the game.
        :param player: Player
        :return: bool
        """
        return self.players.filter(pk=player.pk).exists()

    def has_team(self, team: Team) -> bool:
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

    def setup(self, game_definition_slug: str, room: Room):
        """
        Sets up a Game from a GameDefinition slug and Room.
        :param game_definition_slug:
        :param room: Room
        :return:
        """
        self.__setup_game_defintion(game_definition_slug)
        self.__setup_state_machines()
        self.__setup_from_room(room)
        self.__setup_code()


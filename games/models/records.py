from itertools import chain
from abc import ABC, abstractmethod

from django.db import models
from django.utils.translation import ugettext_lazy as _

from clusterbuster.mixins import TimeStamped
from core.basics.utils import CodeGenerator

from rooms.models import Player, Team, Room
from gamedefinitions.models import State, GameDefinition, StateMachineInterface, GameInterface


class Transition(TimeStamped):
    """
    Transitions record a StateMachine moving from one State to another State.
    """
    reason = models.SlugField(_("Reason"), max_length=32)
    from_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="transitions_out")
    to_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="transitions_in")


class ParameterKey(TimeStamped):
    key = models.SlugField(_("Key"), max_length=128, blank=True, null=True, db_index=True)
    counter = models.IntegerField(_("Counter"), blank=True, null=True, db_index=True)
    player = models.ForeignKey(Player, on_delete=models.SET_NULL, blank=True, null=True, related_name="+")
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, blank=True, null=True, related_name="+")

    def __str__(self):
        return str(self.get())

    def __eq__(self, other):
        if type(other) is not tuple:
            return False
        return self.get() == other

    def get(self):
        return self.key, self.counter, self.player, self.team


class ParameterValue(TimeStamped):
    boolean = models.NullBooleanField(_("Boolean"), default=None)
    integer = models.IntegerField(_("Integer"), null=True, default=None)
    float = models.FloatField(_("Float"), null=True, default=None)

    def __str__(self):
        return str(self.get())

    def __bool__(self):
        if self.boolean:
            return self.boolean
        return False

    def get(self):
        if self.boolean is not None:
            return self.boolean
        elif self.integer is not None:
            return self.integer
        elif self.float is not None:
            return self.float
        else:
            return False


class Parameter(TimeStamped):
    """
    Parameters store all data about a specific game and the state.
    """
    key = models.ForeignKey(ParameterKey, on_delete=models.CASCADE)
    value = models.ForeignKey(ParameterValue, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.key)

    def __bool__(self):
        return bool(self.value)

    def __eq__(self, other):
        if type(other) is not Parameter:
            return False
        return self.value.get() == other.value.get()

    def __ne__(self, other):
        if type(other) is not Parameter:
            return False
        return self.value.get() != other.value.get()

    def __gt__(self, other):
        if type(other) is not Parameter:
            return False
        return self.value.get() > other.value.get()

    def __lt__(self, other):
        if type(other) is not Parameter:
            return False
        return self.value.get() < other.value.get()

    def __ge__(self, other):
        if type(other) is not Parameter:
            return False
        return self.value.get() >= other.value.get()

    def __le__(self, other):
        if type(other) is not Parameter:
            return False
        return self.value.get() <= other.value.get()

    @staticmethod
    def build(composite_key, value):
        parameter_key = None
        parameter_value = None
        if type(composite_key) is tuple:
            key, counter, player, team = composite_key
            parameter_key = ParameterKey(key=key, counter=counter, player=player, team=team)
        if type(value) is int:
            parameter_value = ParameterValue(integer=value)
        elif type(value) is float:
            parameter_value = ParameterValue(float=value)
        elif type(value) is bool:
            parameter_value = ParameterValue(boolean=value)
        if parameter_key and parameter_value:
            parameter_key.save()
            parameter_value.save()
            return Parameter(key=parameter_key, value=parameter_value)


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
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE, related_name="+")

    def __str__(self):
        return str(self.parameter)

    def passes(self):
        return bool(self.parameter.value)


class ComparisonCondition(Condition):
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
        return self.comparison == ComparisonCondition.NOT_EQUAL

    def __is_equal(self):
        return self.comparison == ComparisonCondition.EQUAL

    def __is_gt(self):
        return self.comparison == ComparisonCondition.GREATER_THAN

    def __is_lt(self):
        return self.comparison == ComparisonCondition.LESS_THAN

    def __is_gt_or_equal(self):
        return self.comparison == ComparisonCondition.GREATER_THAN_OR_EQUAL

    def __is_lt_or_equal(self):
        return self.comparison == ComparisonCondition.LESS_THAN_OR_EQUAL

    def __compare_2_parameters(self, number_1, number_2):
        if self.__is_not_equal():
            return number_1 != number_2
        if self.__is_equal():
            return number_1 == number_2
        if self.__is_gt():
            return number_1 > number_2
        if self.__is_lt():
            return number_1 < number_2
        if self.__is_gt_or_equal():
            return number_1 >= number_2
        if self.__is_lt_or_equal():
            return number_1 <= number_2

    def get_readable_comparison(self):
        return self.get_comparison_display()


class ParameterComparisonCondition(ComparisonCondition):
    parameter_1 = models.ForeignKey(Parameter, on_delete=models.CASCADE, related_name="+")
    parameter_2 = models.ForeignKey(Parameter, on_delete=models.CASCADE, related_name="+")

    def __str__(self):
        comparison_str = self.get_comparison_display()
        return str(self.parameter_1) + comparison_str + str(self.parameter_2)

    def passes(self):
        return self.__compare_2_parameters(self.parameter_1, self.parameter_2)


class StateMachine(TimeStamped, StateMachineInterface):
    """
    State Machines manage the State and its Transitions.
    """
    root_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="+")
    previous_state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    current_state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    boolean_conditions = models.ManyToManyField(BooleanCondition, blank=True, related_name="transitions")
    parameter_comparison_conditions = models.ManyToManyField(ParameterComparisonCondition, blank=True,
                                                             related_name="transitions")

    def __transit_to_state(self, state: State):
        self.previous_state = self.current_state
        self.current_state = state
        self.save()

    def get_state(self):
        return self.current_state

    def get_current_rules(self):
        return self.current_state.rules

    def get_conditions(self):
        return list(chain(self.boolean_conditions.all(),
                          self.parameter_comparison_conditions.all()))

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


class Game(TimeStamped, GameInterface):
    """
    Games are instances of Game Definitions, that have codes, State Machines, Players, and Teams.
    """
    game_definition = models.ForeignKey(GameDefinition, on_delete=models.SET_NULL, null=True, blank=True)
    state_machines = models.ManyToManyField(StateMachine, blank=True)
    code = models.SlugField(_("Code"), max_length=16)
    parameters = models.ManyToManyField(Parameter, blank=True)
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
            self.add_state_machine(self.game_definition.root_state)

    def __setup_from_room(self, room: Room):
        """
        :param room: Room
        :return:
        """
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

    def setup(self, game_definition_slug: str, *args, **kwargs):
        """
        Sets up a Game from a GameDefinition slug and Room.
        :param game_definition_slug:
        :param room: Room
        :return:
        """
        self.__setup_game_defintion(game_definition_slug)
        self.__setup_state_machines()
        self.__setup_from_room(kwargs['room'])
        self.__setup_code()

    def add_parameter(self, composite_key, value):
        parameter = Parameter.build(composite_key, value)
        parameter.save()
        self.parameters.add(parameter)
        self.save()

    def add_state_machine(self, state: State):
        state_machine = StateMachine(root_state=state, current_state=state)
        state_machine.save()
        self.state_machines.add(state_machine)
        self.save()


class RuleLibrary(ABC):
    """
    RuleLibraries help map a State's Rules to methods that alter the Game.
    """

    @staticmethod
    @abstractmethod
    def evaluate(state_machine: StateMachine, game: Game):
        """
        :param state_machine: StateMachine
        :param game: Game
        :return:
        """
        pass

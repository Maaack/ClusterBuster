from django.db import models
from django.utils.translation import ugettext_lazy as _

from clusterbuster.mixins import TimeStamped
from core.basics.utils import CodeGenerator

from rooms.models import Player, Team, Room
from gamedefinitions.models import State, GameDefinition
from gamedefinitions.interfaces import StateMachineAbstract, GameAbstract


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
        key = None
        counter = None
        player = None
        team = None
        if type(composite_key) is not tuple:
            raise ValueError('composite_key must be a tuple')
        for composite_key_part in composite_key:
            if type(composite_key_part) is Player:
                player = composite_key_part
            elif type(composite_key_part) is Team:
                team = composite_key_part
            elif type(composite_key_part) is int:
                counter = composite_key_part
            elif type(composite_key_part) is str:
                key = composite_key_part
        if key is None and counter is None and counter is None and key is None:
            raise ValueError('composite_key must contain a string, integer, Player, or Team')
        parameter_key = ParameterKey(key=key, counter=counter, player=player, team=team)
        if type(value) is int:
            parameter_value = ParameterValue(integer=value)
        elif type(value) is float:
            parameter_value = ParameterValue(float=value)
        elif type(value) is bool:
            parameter_value = ParameterValue(boolean=value)
        else:
            raise ValueError('value must be a boolean, integer, or float')
        parameter_key.save()
        parameter_value.save()
        return Parameter(key=parameter_key, value=parameter_value)


class StateMachine(TimeStamped, StateMachineAbstract):
    """
    State Machines manage the State and its Transitions.
    """

    def transit(self, to_state: State, reason=""):
        from_state = self.get_state()
        transition = Transition(state_machine=self, from_state=from_state, to_state=to_state, reason="")
        transition.save()
        self.set_state(to_state)
        self.save()


class Transition(TimeStamped):
    """
    Transitions record a StateMachine moving from one State to another State.
    """
    reason = models.SlugField(_("Reason"), max_length=32)
    state_machine = models.ForeignKey(StateMachine, on_delete=models.CASCADE, related_name="transitions")
    from_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="transitions_out")
    to_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="transitions_in")


class Game(TimeStamped, GameAbstract):
    """
    Games are instances of Game Definitions, that have codes, State Machines, Players, and Teams.
    """
    state_machines = models.ManyToManyField(StateMachine, blank=True)
    parameters = models.ManyToManyField(Parameter, blank=True)
    players = models.ManyToManyField(Player, blank=True, related_name='games')
    teams = models.ManyToManyField(Team, blank=True, related_name='games')
    code = models.SlugField(_("Code"), max_length=16)
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
            self.save()

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
        :return:
        """
        super(Game, self).setup(game_definition_slug, *args, **kwargs)
        self.__setup_state_machines()
        self.__setup_from_room(kwargs['room'])
        self.__setup_code()
        self.save()

    def get_state_machines(self) -> models.QuerySet:
        return self.state_machines

    def get_players(self) -> models.QuerySet:
        return self.players

    def get_teams(self) -> models.QuerySet:
        return self.teams

    def add_parameter(self, composite_key, value):
        """
        Adds a Parameter to the Game object.
        :param composite_key:
        :param value:
        :return:
        """
        parameter = Parameter.build(composite_key, value)
        parameter.save()
        self.parameters.add(parameter)
        self.save()

    def add_state_machine(self, state: State):
        """
        Adds a StateMachine to the Game object.
        :param state: State
        :return:
        """
        state_machine = StateMachine(root_state=state, current_state=state)
        state_machine.save()
        self.state_machines.add(state_machine)
        self.save()


class Condition(TimeStamped):
    """
    Condition wraps a parameter.
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="+")
    to_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="+")

    class Meta:
        abstract = True

    def passes(self):
        return False

    def get_next_state(self):
        return self.to_state


class BooleanCondition(Condition):
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE, related_name="+")

    def __str__(self):
        return str(self.parameter)

    def passes(self):
        return bool(self.parameter.value)


class ComparisonConditionAbstract(Condition):
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
        return self.comparison == ComparisonConditionAbstract.NOT_EQUAL

    def __is_equal(self):
        return self.comparison == ComparisonConditionAbstract.EQUAL

    def __is_gt(self):
        return self.comparison == ComparisonConditionAbstract.GREATER_THAN

    def __is_lt(self):
        return self.comparison == ComparisonConditionAbstract.LESS_THAN

    def __is_gt_or_equal(self):
        return self.comparison == ComparisonConditionAbstract.GREATER_THAN_OR_EQUAL

    def __is_lt_or_equal(self):
        return self.comparison == ComparisonConditionAbstract.LESS_THAN_OR_EQUAL

    def __compare_2(self, number_1, number_2):
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


class ComparisonCondition(ComparisonConditionAbstract):
    parameter_1 = models.ForeignKey(Parameter, on_delete=models.CASCADE, related_name="+")
    parameter_2 = models.ForeignKey(Parameter, on_delete=models.CASCADE, related_name="+")

    def __str__(self):
        comparison_str = self.get_comparison_display()
        return str(self.parameter_1) + comparison_str + str(self.parameter_2)

    def passes(self):
        return self.__compare_2(self.parameter_1, self.parameter_2)



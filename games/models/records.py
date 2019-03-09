from django.db import models
from django.utils.translation import ugettext_lazy as _

from clusterbuster.mixins import TimeStamped
from core.basics.utils import CodeGenerator

from rooms.models import Player, Team, Room
from gamedefinitions.models import State, GameDefinition
from gamedefinitions.interfaces import (
    StateMachineAbstract, GameAbstract,
    BooleanConditionAbstract, ComparisonConditionAbstract
)


class Game(GameAbstract):
    """
    Games are instances of Game Definitions, that have codes, State Machines, Players, and Teams.
    """
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

    def get_parameter(self, **kwargs):
        try:
            parameter_key = ParameterKey.objects.filter(parameter__game=self, **kwargs).get()
        except ParameterKey.DoesNotExist:
            parameter_key = ParameterKey.objects.create(**kwargs)
        try:
            parameter = Parameter.objects.filter(game=self, key=parameter_key).get()
        except Parameter.DoesNotExist:
            parameter_value = ParameterValue.objects.create()
            parameter = Parameter(game=self, key=parameter_key, value=parameter_value)
        return parameter

    def add_parameter(self, key_dict, value):
        """
        Adds a Parameter to the Game object.
        :param key_dict:
        :param value:
        :return:
        """
        parameter = self.get_parameter(**key_dict)
        parameter.set_value(value)
        if self.parameters.filter(id=parameter.id).first() is None:
            self.parameters.add(parameter)
            self.save()

    def add_state_machine(self, state_slug: str):
        """
        Adds a StateMachine to the Game object.
        :param state_slug: str
        :return:
        """
        try:
            state = State.objects.get(label=state_slug)
        except State.DoesNotExist:
            raise ValueError('state_slug must be a valid existing state')
        try:
            self.state_machines.filter(root_state=state).get()
        except StateMachine.DoesNotExist:
            state_machine = StateMachine.objects.create(root_state=state, current_state=state)
            self.state_machines.add(state_machine)
            self.save()

    def add_condition(self, state_machine, condition_query_set):
        """
        :param state_machine: StateMachineAbstract
        :param condition_query_set: models.QuerySet
        :return:
        """
        pass


class StateMachine(StateMachineAbstract):
    """
    State Machines manage the State and its Transitions.
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="state_machines")

    def transit(self, to_state: State, reason=""):
        from_state = self.get_state()
        transition = Transition(state_machine=self, from_state=from_state, to_state=to_state, reason="")
        transition.save()
        self.set_state(to_state)
        self.save()

    def evaluate_conditions(self):
        for condition in self.boolean_conditions.all():
            if condition.passes():
                next_state = condition.get_next_state()
                self.transit(next_state, str(condition.parameter.key))
        for condition in self.comparison_conditions.all():
            if condition.passes():
                next_state = condition.get_next_state()
                self.transit(next_state, str(condition.parameter_1.key))

    def get_game_parameter(self, **kwargs):
        return self.game.get_parameter(**kwargs)

    def add_comparison_condition(self, key_dict_1, key_dict_2, comparison, to_state):
        parameter_1 = self.get_game_parameter(**key_dict_1)
        parameter_2 = self.get_game_parameter(**key_dict_2)
        self.comparison_conditions.get_or_create(parameter_1=parameter_1, parameter_2=parameter_2,
                                                 comparison=comparison, to_state=to_state)

    def add_boolean_condition(self, key_dict, to_state):
        parameter = self.get_game_parameter(**key_dict)
        self.boolean_conditions.get_or_create(parameter=parameter, to_state=to_state)


class Transition(TimeStamped):
    """
    Transitions record a StateMachine moving from one State to another State.
    """
    reason = models.SlugField(_("Reason"), max_length=32)
    state_machine = models.ForeignKey(StateMachine, on_delete=models.CASCADE, related_name="transitions")
    from_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="transitions_out")
    to_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="transitions_in")


class ParameterKey(TimeStamped):
    key = models.SlugField(_("Key"), max_length=128, blank=True, null=True, db_index=True)
    counter = models.IntegerField(_("Counter"), blank=True, null=True, db_index=True)
    player = models.ForeignKey(Player, on_delete=models.SET_NULL, blank=True, null=True, related_name="+")
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, blank=True, null=True, related_name="+")

    def __str__(self):
        return str(self.get_tuple())

    def get_tuple(self):
        result = tuple()
        if self.key is not None:
            result = result + (self.key,)
        if self.counter is not None:
            result = result + (self.counter,)
        if self.player is not None:
            result = result + (self.player,)
        if self.team is not None:
            result = result + (self.team,)
        return result


class ParameterValue(TimeStamped):
    boolean = models.NullBooleanField(_("Boolean"), default=None)
    integer = models.IntegerField(_("Integer"), null=True, default=None)
    float = models.FloatField(_("Float"), null=True, default=None)
    player = models.ForeignKey(Player, on_delete=models.SET_NULL, blank=True, null=True, related_name="+")
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, blank=True, null=True, related_name="+")

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
        elif self.player is not None:
            return self.player
        elif self.team is not None:
            return self.team
        else:
            return None


class Parameter(TimeStamped):
    """
    Parameters store all data about a specific game and the state.
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="parameters")
    key = models.OneToOneField(ParameterKey, on_delete=models.CASCADE, related_name="parameter")
    value = models.OneToOneField(ParameterValue, on_delete=models.CASCADE, related_name="parameter")

    class Meta:
        unique_together = ('game', 'key')

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

    def save(self, *args, **kwargs):
        if self.value is None:
            self.value = ParameterValue.objects.create()
        super(Parameter, self).save(*args, **kwargs)

    def get_value(self):
        self.value.get()

    def set_value(self, value):
        if type(value) is int:
            parameter_value = ParameterValue(integer=value)
        elif type(value) is float:
            parameter_value = ParameterValue(float=value)
        elif type(value) is bool:
            parameter_value = ParameterValue(boolean=value)
        elif type(value) is Player:
            parameter_value = ParameterValue(player=value)
        elif type(value) is Team:
            parameter_value = ParameterValue(team=value)
        else:
            raise ValueError('value must be a boolean, integer, or float')
        parameter_value.save()
        self.value = parameter_value
        self.save()


class BooleanCondition(BooleanConditionAbstract):
    state_machine = models.ForeignKey(StateMachine, on_delete=models.CASCADE, related_name="boolean_conditions")
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE, related_name="+")

    def __str__(self):
        return str(self.parameter)

    def passes(self):
        return bool(self.parameter.value)


class ComparisonCondition(ComparisonConditionAbstract):
    state_machine = models.ForeignKey(StateMachine, on_delete=models.CASCADE, related_name="comparison_conditions")
    parameter_1 = models.ForeignKey(Parameter, on_delete=models.CASCADE, related_name="+")
    parameter_2 = models.ForeignKey(Parameter, on_delete=models.CASCADE, related_name="+")

    def __str__(self):
        comparison_str = self.get_comparison_display()
        return str(self.parameter_1) + comparison_str + str(self.parameter_2)

    def passes(self):
        return self.__compare_2(self.parameter_1, self.parameter_2)



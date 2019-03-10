from django.db import models
from django.utils.translation import ugettext_lazy as _

from clusterbuster.mixins import TimeStamped
from core.basics.utils import CodeGenerator

from rooms.models import Player, Team, Room
from gamedefinitions.models import State, GameDefinition
from gamedefinitions.interfaces import (
    StateMachineAbstract, GameAbstract, ConditionAbstract,
    ComparisonConditionAbstract,
    ConditionalTransitionAbstract
)


class Game(GameAbstract, TimeStamped):
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
            self.add_state_machine(self.game_definition.root_state.label)

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
            parameter_key = self.parameter_keys.filter(game=self, **kwargs).get()
        except ParameterKey.DoesNotExist:
            parameter_key = self.parameter_keys.create(**kwargs)
        try:
            parameter = self.parameters.filter(key=parameter_key).get()
        except Parameter.DoesNotExist:
            parameter = Parameter(game=self, key=parameter_key)
            parameter.save()
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
            state_machine = self.state_machines.filter(root_state=state).get()
        except StateMachine.DoesNotExist:
            state_machine = self.state_machines.create(root_state=state, current_state=state)
        return state_machine


class StateMachine(StateMachineAbstract, TimeStamped):
    """
    State Machines manage the State and its Transitions.
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="state_machines")

    def transit(self, to_state: State, reason=""):
        from_state = self.get_state()
        transition = Transition(state_machine=self, from_state=from_state, to_state=to_state, reason=reason)
        transition.save()
        self.set_state(to_state)
        self.save()

    def evaluate_conditions(self):
        for conditional_transition in self.conditional_transitions.all():
            if conditional_transition.from_state == self.current_state and conditional_transition.passes():
                to_state = conditional_transition.to_state
                self.transit(to_state, str(conditional_transition))

    def get_game_parameter(self, **kwargs):
        return self.game.get_parameter(**kwargs)

    def get_condition_transition(self):
        pass

    def add_conditional_transition(self, label: str, to_state_slug: str):
        from_state = self.get_state()
        to_state = State.objects.get(label=to_state_slug)
        conditional_transition, created = self.conditional_transitions.get_or_create(state_machine=self, label=label,
                                                                                     from_state=from_state,
                                                                                     to_state=to_state)
        return conditional_transition


class Transition(TimeStamped):
    """
    Transitions record a StateMachine moving from one State to another State.
    """
    reason = models.SlugField(_("Reason"), max_length=32)
    state_machine = models.ForeignKey(StateMachine, on_delete=models.CASCADE, related_name="transitions")
    from_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="transitions_out")
    to_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="transitions_in")


class ParameterKey(TimeStamped):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="parameter_keys")
    key = models.SlugField(_("Key"), max_length=128, blank=True, null=True, db_index=True)
    counter = models.IntegerField(_("Counter"), blank=True, null=True, db_index=True)
    player = models.ForeignKey(Player, on_delete=models.SET_NULL, blank=True, null=True, related_name="+")
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, blank=True, null=True, related_name="+")

    def __str__(self):
        return str(self.get_list())

    def get_list(self):
        result = list()
        if self.key is not None:
            result.append(self.key)
        if self.counter is not None:
            result.append(self.counter)
        if self.player is not None:
            result.append(self.player)
        if self.team is not None:
            result.append(self.team)
        return result


class ParameterValue(TimeStamped):
    boolean = models.NullBooleanField(_("Boolean"), default=None)
    integer = models.IntegerField(_("Integer"), blank=True, null=True, default=None)
    float = models.FloatField(_("Float"), blank=True, null=True, default=None)
    string = models.CharField(_("String"), max_length=255, blank=True, null=True, default=None)
    player = models.ForeignKey(Player, on_delete=models.SET_NULL, blank=True, null=True, related_name="+")
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, blank=True, null=True, related_name="+")

    def __str__(self):
        return str(self.parameter) + ": " + str(self.get())

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
        elif self.string is not None:
            return self.string
        elif self.player is not None:
            return self.player
        elif self.team is not None:
            return self.team
        else:
            return None

    def set(self, value):
        if type(value) is int:
            self.integer=value
        elif type(value) is float:
            self.float = value
        elif type(value) is str:
            self.string = value
        elif type(value) is bool:
            self.boolean = value
        elif type(value) is Player:
            self.player = value
        elif type(value) is Team:
            self.team = value
        else:
            raise ValueError('value must be a boolean, integer, or float')
        self.save()


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
        try:
            self.value.get()
        except ParameterValue.DoesNotExist:
            self.value = ParameterValue.objects.create(parameter=self)
        super(Parameter, self).save(*args, **kwargs)

    def get_value(self):
        self.value.get()

    def set_value(self, value_variable):
        try:
            value = self.value
        except ParameterValue.DoesNotExist:
            value = ParameterValue()
            value.set(value_variable)
            value.save()
            self.value = value
            self.save()
        value.set(value_variable)


class Condition(ConditionAbstract, TimeStamped):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="conditions")
    parameter_1 = models.ForeignKey(Parameter, on_delete=models.SET_NULL, blank=True, null=True, related_name="+")
    parameter_2 = models.ForeignKey(Parameter, on_delete=models.SET_NULL, blank=True, null=True, related_name="+")

    def __str__(self):
        if self.is_comparison():
            comparison_str = self.get_readable_comparison()
            return str(self.parameter_1) + comparison_str + str(self.parameter_2)
        return str(self.parameter_1.key)

    def passes(self):
        if self.is_has_value():
            return self.parameter_1.value.get() is not None
        elif self.is_boolean():
            return bool(self.parameter_1.value)
        elif self.is_comparison():
            return self.compare_2_numbers(self.parameter_1, self.parameter_2)


class ConditionalTransition(ConditionalTransitionAbstract, TimeStamped):
    state_machine = models.ForeignKey(StateMachine, on_delete=models.CASCADE, related_name="conditional_transitions")
    conditions = models.ManyToManyField(Condition, related_name="conditional_transitions")

    class Meta:
        unique_together = ('state_machine', 'label', 'from_state', 'to_state')

    def passes(self):
        for condition in self.conditions.all():
            if condition.passes():
                if self.is_or_op():
                    return True
            elif self.is_and_op():
                return False
        if self.is_or_op():
            return False
        return True

    def add_has_value_condition(self, key_dict) -> ConditionAbstract:
        parameter = self.state_machine.get_game_parameter(**key_dict)
        condition, created = self.conditions.get_or_create(condition_type=ConditionAbstract.HAS_VALUE,
                                                           parameter_1=parameter, )
        self.save()
        return condition

    def add_boolean_condition(self, key_dict) -> ConditionAbstract:
        parameter = self.state_machine.get_game_parameter(**key_dict)
        condition, created = self.conditions.get_or_create(condition_type=ConditionAbstract.BOOLEAN,
                                                           parameter_1=parameter)
        self.save()
        return condition

    def add_comparison_condition(self, key_dict_1, key_dict_2, comparison_type) -> ConditionAbstract:
        parameter_1 = self.state_machine.get_game_parameter(**key_dict_1)
        parameter_2 = self.state_machine.get_game_parameter(**key_dict_2)
        condition, created = self.conditions.get_or_create(game=self.state_machine.game, condition_type=ConditionAbstract.COMPARISON,
                                                           parameter_1=parameter_1,
                                                           parameter_2=parameter_2, comparison_type=comparison_type)
        self.save()
        return condition


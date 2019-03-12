from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from clusterbuster.mixins import TimeStamped, CodeGenerator

from rooms.models import Player, Team, Room
from gamedefinitions.models import State, GameDefinition
from gamedefinitions.interfaces import (
    StateMachineAbstract, GameAbstract, ConditionAbstract, ParameterAbstract,
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

    @staticmethod
    def __get_value_param_type(raw_value):
        if isinstance(
                raw_value, int) or isinstance(
                raw_value, float) or isinstance(
                raw_value, str) or isinstance(
                raw_value, bool):
            return MixedValue
        else:
            return type(raw_value)

    @staticmethod
    def __get_key_from_args(*args):
        key_string = "_".join(str(i).lower() for i in args)
        print("HOW IS THIS!?!??!?!")
        print(key_string)
        return key_string

    @staticmethod
    def __get_model_value(raw_value):
        value_type = Game.__get_value_param_type(raw_value)
        if value_type == MixedValue:
            value = value_type()
            value.set(raw_value)
            return value
        elif isinstance(raw_value, models.Model):
            return raw_value

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

    def get_parameter(self, key_args):
        if isinstance(key_args, str):
            key_args = (key_args,)
        key_string = Game.__get_key_from_args(*key_args)
        parameter, create = Parameter.objects.get_or_create(game=self, key=key_string)
        return parameter

    def get_parameter_value(self, key_args):
        parameter = self.get_parameter(key_args)
        if isinstance(parameter.value, MixedValue):
            parameter.value.get()
        return parameter.value

    def set_parameter_value(self, key_args, value):
        parameter = self.get_parameter(key_args)
        parameter.set_value(Game.__get_model_value(value))
        parameter.save()

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

    def get_game_parameter(self, key_args):
        return self.game.get_parameter(key_args)

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


class MixedValue(TimeStamped):
    integer = models.IntegerField(_("Integer"), blank=True, null=True, default=None)
    string = models.CharField(_("String"), max_length=255, blank=True, null=True, default=None)
    boolean = models.NullBooleanField(_("Boolean"), default=None)
    float = models.FloatField(_("Float"), blank=True, null=True, default=None)

    def __str__(self):
        return str(self.get())

    def __bool__(self):
        if self.boolean:
            return self.boolean
        return False

    def __eq__(self, other):
        if not isinstance(other, MixedValue):
            return False
        return self.get_number() == other.get_number()

    def __ne__(self, other):
        if not isinstance(other, MixedValue):
            return False
        return self.get_number() != other.get_number()

    def __gt__(self, other):
        if not isinstance(other, MixedValue):
            return False
        return self.get_number() > other.get_number()

    def __lt__(self, other):
        if not isinstance(other, MixedValue):
            return False
        return self.get_number() < other.get_number()

    def __ge__(self, other):
        if not isinstance(other, MixedValue):
            return False
        return self.get_number() >= other.get_number()

    def __le__(self, other):
        if not isinstance(other, MixedValue):
            return False
        return self.get_number() <= other.get_number()

    def get(self):
        if self.boolean is not None:
            return self.boolean
        elif self.float is not None:
            return self.float
        elif self.integer is not None:
            return self.integer
        elif self.string is not None:
            return self.string
        else:
            return None

    def get_number(self):
        if self.integer is not None:
            return self.integer
        elif self.float is not None:
            return self.float
        return None

    def set(self, value):
        if isinstance(value, float):
            self.float = value
        elif isinstance(value, bool):
            self.boolean = value
        elif isinstance(value, int):
            self.integer = value
        elif isinstance(value, str):
            self.string = value
        else:
            raise ValueError('value must be a boolean, integer, float, or string')
        self.save()


class Parameter(TimeStamped, ParameterAbstract):
    """
    Parameters store all data about a specific game and the state.
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="parameters")
    key = models.SlugField(_("Key"), max_length=255, db_index=True)
    value = GenericForeignKey('content_type', 'object_id')
    object_id = models.PositiveIntegerField(_('Object ID'), blank=True, null=True,)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        unique_together = ('game', 'key')

    def get_key(self):
        return self.key

    def get_value(self):
        return self.value

    def set_value(self, value):
        self.value = value
        self.save()


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
            return self.parameter_1.get_value() is not None
        elif self.is_boolean():
            return bool(self.parameter_1.get_value())
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

    def add_has_value_condition(self, key_args) -> ConditionAbstract:
        parameter = self.state_machine.get_game_parameter(key_args)
        condition, created = self.conditions.get_or_create(game=self.state_machine.game,
                                                           condition_type=ConditionAbstract.HAS_VALUE,
                                                           parameter_1=parameter)
        self.save()
        return condition

    def add_boolean_condition(self, key_args) -> ConditionAbstract:
        parameter = self.state_machine.get_game_parameter(key_args)
        condition, created = self.conditions.get_or_create(game=self.state_machine.game,
                                                           condition_type=ConditionAbstract.BOOLEAN,
                                                           parameter_1=parameter)
        self.save()
        return condition

    def add_comparison_condition(self, key_args_1, key_args_2, comparison_type) -> ConditionAbstract:
        parameter_1 = self.state_machine.get_game_parameter(key_args_1)
        parameter_2 = self.state_machine.get_game_parameter(key_args_2)
        condition, created = self.conditions.get_or_create(game=self.state_machine.game,
                                                           condition_type=ConditionAbstract.COMPARISON,
                                                           parameter_1=parameter_1,
                                                           parameter_2=parameter_2, comparison_type=comparison_type)
        self.save()
        return condition


from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse

from clusterbuster.mixins import TimeStamped, CodeGenerator

from lobbies.models import Player, Team, Lobby
from gamedefinitions.models import State, Rule
from gamedefinitions.interfaces import (
    StateMachineAbstract, GameAbstract, ConditionAbstract, ConditionGroupAbstract, RuleLibrary,
)

from .parameters import ParameterDictionary, Parameter

__all__ = ['Game', 'StateMachine', 'Transition', 'Condition', 'ConditionGroup', 'Trigger']


class Game(GameAbstract, TimeStamped):
    """
    Games are instances of Game Definitions, that have codes, State Machines, Players, and Teams.
    """
    players = models.ManyToManyField(Player, blank=True, related_name='games')
    teams = models.ManyToManyField(Team, blank=True, related_name='games')
    code = models.SlugField(_("Code"), max_length=16)
    lobby = models.ForeignKey(Lobby, on_delete=models.SET_NULL, null=True, blank=True, related_name='games')
    leader = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    parameters = models.ForeignKey(ParameterDictionary, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="+")

    class Meta:
        verbose_name = _("Game")
        verbose_name_plural = _("Games")
        ordering = ["-created"]

    def __str__(self):
        return str(self.code)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trigger_list = []
        self.parameters_updated = False

    def __setup_parameters(self):
        if self.parameters is None:
            self.parameters = ParameterDictionary.objects.create()
            self.save()

    def __setup_state_parameters(self):
        if self.game_definition:
            for state in self.game_definition.states.all():
                parameter_key = state.slug + "_state"
                self.set_parameter_value(parameter_key, state)

    def __setup_state_machines(self):
        if self.game_definition:
            for state_machine in self.game_definition.state_machines.all():
                parameter_key = state_machine.slug
                self.add_state_machine(parameter_key, state_machine.root_state)

    def __setup_code(self):
        if not self.code:
            self.code = CodeGenerator.game_code()
            self.save()

    def __setup_from_lobby(self, lobby: Lobby):
        """
        :param lobby: Lobby
        :return:
        """
        self.lobby = lobby
        self.players.set(lobby.players.all())
        self.teams.set(lobby.teams.all())
        game_url = reverse('game_detail', kwargs={'slug': self.code})
        self.lobby.start_activity('Cluster Buster', game_url)

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
        Returns `True` if the team is in the lobby.
        :param team: Team
        :return: bool
        """
        return self.teams.filter(pk=team.pk).exists()

    def has(self, model_object) -> bool:
        """
        Returns `True` if the lobby has the player or team in it.
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
        Sets up a Game from a GameDefinition slug and Lobby.
        :param game_definition_slug:
        :return:
        """
        super(Game, self).setup(game_definition_slug, *args, **kwargs)
        self.__setup_parameters()
        self.__setup_state_parameters()
        self.__setup_state_machines()
        self.__setup_code()
        self.__setup_from_lobby(kwargs['lobby'])
        self.save()

    def start(self, rule_library: RuleLibrary):
        if self.game_definition:
            first_rule = self.game_definition.first_rule
            self.evaluate_rule(first_rule, rule_library)

    def update(self, rule_library: RuleLibrary):
        self.trigger_list = list(self.triggers.filter(active=True).all())
        self.parameters_updated = True
        while self.parameters_updated:
            active_trigger_list = self.trigger_list.copy()
            self.parameters_updated = False
            while len(active_trigger_list) > 0:
                trigger = active_trigger_list.pop()
                trigger.squeeze(rule_library)

    def evaluate_rule(self, rule: Rule, rule_library: RuleLibrary):
        rule_method = self.get_rule_method(rule, rule_library)
        if rule_method is not None:
            rule_method(self)

    def get_rule_method(self, rule: Rule, rule_library: RuleLibrary):
        prefix = self.game_definition.slug + "_"
        prefix_length = len(prefix)
        rule_slug = rule.slug
        if rule_slug.startswith(prefix):
            rule_slug = rule_slug[prefix_length:]
        print("%s rule lookup" % (rule_slug,))
        try:
            return rule_library.method_map(rule_slug)
        except KeyError:
            print("%s didn't exist" % (rule_slug,))
            return None

    def get_parameter(self, key_args):
        return self.parameters.get_parameter(key_args)

    def get_parameter_value(self, key_args):
        return self.parameters.get_parameter_value(key_args)

    def set_parameter_value(self, key_args, value):
        self.parameters.set_parameter_value(key_args, value)
        self.parameters_updated = True

    def prepend_game_slug(self, slug):
        game_definition_slug = self.game_definition.slug
        return game_definition_slug + "_" + slug

    def add_state_machine(self, key_args, state: State):
        """
        Adds a StateMachine to the Game object.
        :param key_args: mixed
        :param state: State
        :return:
        """
        state_machine = self.state_machines.create(root_state=state, current_state=state)
        self.set_parameter_value(key_args, state_machine)
        return state_machine

    def add_trigger(self, rule_slug: str):
        """
        Adds a Trigger to the Game object.
        :param rule_slug:
        :return:
        """
        rule_slug = self.prepend_game_slug(rule_slug)
        condition_group = self.condition_groups.create()
        try:
            rule = Rule.objects.get(slug=rule_slug)
        except Rule.DoesNotExist:
            raise ValueError('rule_slug must match the label of an existing Rule')
        trigger = self.triggers.create(condition_group=condition_group, rule=rule)
        self.trigger_list.append(trigger)
        self.parameters_updated = True
        return trigger

    def transit_state_machine(self, key_args, state_slug: str, reason: str):
        state_machine = self.get_parameter_value(key_args)  # type: StateMachine
        try:
            state = State.objects.get(slug=state_slug)
        except State.DoesNotExist:
            raise ValueError('state_slug must match the label of an existing State')
        state_machine.transit(state, reason)
        self.parameters_updated = True


class StateMachine(StateMachineAbstract, TimeStamped):
    """
    State Machines manage the State and its Transitions.
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="state_machines")

    def __str__(self):
        return str(self.game) + " - " + str(self.current_state)

    def transit(self, to_state: State, reason=""):
        from_state = self.get_state()
        transition = Transition(state_machine=self, from_state=from_state, to_state=to_state, reason=reason)
        transition.save()
        self.set_state(to_state)
        self.save()


class Transition(TimeStamped):
    """
    Transitions record a StateMachine moving from one State to another State.
    """
    reason = models.SlugField(_("Reason"), max_length=32)
    state_machine = models.ForeignKey(StateMachine, on_delete=models.CASCADE, related_name="transitions")
    from_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="+")
    to_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="+")


class Condition(ConditionAbstract, TimeStamped):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="conditions")
    parameter_1 = models.ForeignKey(Parameter, on_delete=models.SET_NULL, blank=True, null=True, related_name="+")
    parameter_2 = models.ForeignKey(Parameter, on_delete=models.SET_NULL, blank=True, null=True, related_name="+")

    def __str__(self):
        if self.is_comparison():
            comparison_str = self.get_readable_comparison()
            return str(self.parameter_1) + ' ' + comparison_str + ' ' + str(self.parameter_2)
        return str(self.parameter_1)

    def passes(self):
        if self.is_has_value():
            return self.parameter_1.value is not None
        elif self.is_boolean():
            return bool(self.parameter_1.value)
        elif self.is_comparison():
            return self.compare_2_numbers(self.parameter_1, self.parameter_2)
        elif self.is_fsm_state():
            state_machine = self.parameter_1.value  # type: StateMachine
            return state_machine.current_state == self.parameter_2.value


class ConditionGroup(ConditionGroupAbstract, TimeStamped):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="condition_groups")
    conditions = models.ManyToManyField(Condition, related_name="condition_groups")

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
        parameter = self.game.get_parameter(key_args)
        condition, created = self.conditions.get_or_create(game=self.game,
                                                           condition_type=ConditionAbstract.HAS_VALUE,
                                                           parameter_1=parameter)
        self.save()
        return condition

    def add_boolean_condition(self, key_args) -> ConditionAbstract:
        parameter = self.game.get_parameter(key_args)
        condition, created = self.conditions.get_or_create(game=self.game,
                                                           condition_type=ConditionAbstract.BOOLEAN,
                                                           parameter_1=parameter)
        self.save()
        return condition

    def add_comparison_condition(self, key_args_1, key_args_2, comparison_type) -> ConditionAbstract:
        parameter_1 = self.game.get_parameter(key_args_1)
        parameter_2 = self.game.get_parameter(key_args_2)
        condition, created = self.conditions.get_or_create(game=self.game,
                                                           condition_type=ConditionAbstract.COMPARISON,
                                                           parameter_1=parameter_1,
                                                           parameter_2=parameter_2, comparison_type=comparison_type)
        self.save()
        return condition

    def add_fsm_state_condition(self, key_args_1, key_args_2) -> ConditionAbstract:
        parameter_1 = self.game.get_parameter(key_args_1)
        parameter_2 = self.game.get_parameter(key_args_2)
        if not isinstance(parameter_1.value, StateMachine):
            raise ValueError('parameter_1 must be an instance of StateMachine')
        if not isinstance(parameter_2.value, State):
            raise ValueError('parameter_2 must be an instance of State')
        condition, created = self.conditions.get_or_create(game=self.game,
                                                           condition_type=ConditionAbstract.FSM_STATE,
                                                           parameter_1=parameter_1,
                                                           parameter_2=parameter_2)
        self.save()
        return condition


class Trigger(TimeStamped):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="triggers")
    condition_group = models.ForeignKey(ConditionGroup, on_delete=models.CASCADE, related_name="triggers")
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE, related_name="+")
    active = models.BooleanField(_("Active"), db_index=True, default=True)
    repeats = models.BooleanField(_("Repeats"), default=False)
    trigger_count = models.PositiveSmallIntegerField(_("Trigger Count"), default=0)

    def __str__(self):
        return str(self.game) + " - " + str(self.rule)

    def squeeze(self, rule_library: RuleLibrary):
        if self.active is False:
            return
        if self.condition_group.passes():
            self.pull(rule_library)

    def pull(self, rule_library: RuleLibrary):
        self.trigger_count += 1
        self.game.evaluate_rule(self.rule, rule_library)
        if self.repeats is False:
            self.active = False
        self.save()

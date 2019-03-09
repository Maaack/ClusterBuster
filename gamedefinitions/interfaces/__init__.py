from itertools import chain
from abc import ABC, abstractmethod

from django.db import models
from django.utils.translation import ugettext_lazy as _

from clusterbuster.mixins import TimeStamped

from gamedefinitions.models import State, GameDefinition


class StateMachineAbstract(TimeStamped):
    root_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="+")
    current_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="+")
    previous_state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")

    class Meta:
        abstract = True

    def get_state(self):
        return self.current_state

    def set_state(self, state: State):
        self.previous_state = self.current_state
        self.current_state = state
        self.save()

    def get_rules(self):
        return self.current_state.rules

    def transit(self, state: State, reason: str):
        raise NotImplementedError('StateMachineAbstract subclasses must override transit()')

    def add_comparison_condition(self, key_dict_1, key_dict_2, comparison, to_state):
        raise NotImplementedError('StateMachineAbstract subclasses must override add_comparison_condition()')

    def add_boolean_condition(self, key_dict, to_state):
        raise NotImplementedError('StateMachineAbstract subclasses must override add_boolean_condition()')


class ConditionAbstract(TimeStamped):
    """
    Condition wraps a parameter.
    """
    to_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="+")

    class Meta:
        abstract = True

    def passes(self):
        return False

    def get_next_state(self):
        return self.to_state


class BooleanConditionAbstract(ConditionAbstract):
    class Meta:
        abstract = True


class ComparisonConditionAbstract(ConditionAbstract):
    NOT_EQUAL = 0
    EQUAL = 1
    GREATER_THAN = 2
    LESS_THAN = 3
    GREATER_THAN_OR_EQUAL = 4
    LESS_THAN_OR_EQUAL = 5
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


class GameAbstract(TimeStamped):
    """
    RuleLibraries help map a State's Rules to methods that alter the Game.
    """
    game_definition = models.ForeignKey(GameDefinition, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        abstract = True

    def __setup_game_definition(self, game_definition_slug: str):
        """
        :param game_definition_slug: str
        :return:
        """
        self.game_definition = GameDefinition.objects.get(slug=game_definition_slug)
        self.save()

    def setup(self, game_definition_slug: str, *args, **kwargs):
        self.__setup_game_definition(game_definition_slug)

    def get_state_machines(self) -> models.QuerySet:
        raise NotImplementedError('GameAbstract subclasses must override get_state_machines()')

    def get_players(self) -> models.QuerySet:
        raise NotImplementedError('GameAbstract subclasses must override get_players()')

    def get_teams(self) -> models.QuerySet:
        raise NotImplementedError('GameAbstract subclasses must override get_teams()')

    def get_parameter(self, key):
        raise NotImplementedError('GameAbstract subclasses must override get_parameter()')

    def add_parameter(self, key, value):
        raise NotImplementedError('GameAbstract subclasses must override add_parameter()')

    def add_state_machine(self, state_slug: str):
        raise NotImplementedError('GameAbstract subclasses must override add_state_machine()')


class RuleLibrary(ABC):
    """
    RuleLibraries help map a State's Rules to methods that alter the Game.
    """

    @staticmethod
    @abstractmethod
    def evaluate(game: GameAbstract):
        """
        :param game: GameAbstract
        :return:
        """
        pass

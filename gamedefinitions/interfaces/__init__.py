from abc import ABC, abstractmethod

from django.db import models
from django.utils.translation import ugettext_lazy as _

from gamedefinitions.models import State, GameDefinition


class ConditionAbstractBase(models.Model):
    HAS_VALUE = 0
    BOOLEAN = 1
    COMPARISON = 2
    CONDITION_TYPE_CHOICES = (
        (HAS_VALUE, "Has Value"),
        (BOOLEAN, "Boolean"),
        (COMPARISON, "Comparison"),
    )
    condition_type = models.PositiveSmallIntegerField(_("Condition Operation"), choices=CONDITION_TYPE_CHOICES,
                                                      default=HAS_VALUE)

    class Meta:
        abstract = True

    def is_has_value(self):
        return self.condition_type == ConditionAbstract.HAS_VALUE

    def is_boolean(self):
        return self.condition_type == ConditionAbstract.BOOLEAN

    def is_comparison(self):
        return self.condition_type == ConditionAbstract.COMPARISON

    def passes(self):
        raise NotImplementedError('ConditionAbstract subclasses must override passes()')


class ComparisonConditionAbstract(models.Model):
    EQUAL = 0
    NOT_EQUAL = 1
    GREATER_THAN = 2
    LESS_THAN = 3
    GREATER_THAN_OR_EQUAL = 4
    LESS_THAN_OR_EQUAL = 5
    COMPARISON_TYPE_CHOICES = (
        (EQUAL, "=="),
        (NOT_EQUAL, "!="),
        (GREATER_THAN, ">"),
        (LESS_THAN, "<"),
        (GREATER_THAN_OR_EQUAL, ">="),
        (LESS_THAN_OR_EQUAL, "<="),
    )

    comparison_type = models.PositiveSmallIntegerField(_("Comparison Operation"), choices=COMPARISON_TYPE_CHOICES,
                                                       default=EQUAL)

    class Meta:
        abstract = True

    def __is_equal(self):
        return self.comparison_type == ComparisonConditionAbstract.EQUAL

    def __is_not_equal(self):
        return self.comparison_type == ComparisonConditionAbstract.NOT_EQUAL

    def __is_gt(self):
        return self.comparison_type == ComparisonConditionAbstract.GREATER_THAN

    def __is_lt(self):
        return self.comparison_type == ComparisonConditionAbstract.LESS_THAN

    def __is_gt_or_equal(self):
        return self.comparison_type == ComparisonConditionAbstract.GREATER_THAN_OR_EQUAL

    def __is_lt_or_equal(self):
        return self.comparison_type == ComparisonConditionAbstract.LESS_THAN_OR_EQUAL

    def compare_2_numbers(self, number_1, number_2):
        if self.__is_equal():
            return number_1 == number_2
        if self.__is_not_equal():
            return number_1 != number_2
        if self.__is_gt():
            return number_1 > number_2
        if self.__is_lt():
            return number_1 < number_2
        if self.__is_gt_or_equal():
            return number_1 >= number_2
        if self.__is_lt_or_equal():
            return number_1 <= number_2

    def get_readable_comparison(self):
        return self.get_comparison_type_display()


class ConditionAbstract(ConditionAbstractBase, ComparisonConditionAbstract):
    class Meta:
        abstract = True

    def passes(self):
        raise NotImplementedError('ConditionAbstract subclasses must override passes()')


class ConditionGroupAbstract(models.Model):
    OR_OP = 0
    AND_OP = 1
    BOOLEAN_OP_CHOICES = (
        (OR_OP, "OR"),
        (AND_OP, "AND"),
    )

    boolean_op = models.PositiveSmallIntegerField(_("Boolean Operation"), choices=BOOLEAN_OP_CHOICES, default=OR_OP)

    class Meta:
        abstract = True

    def is_or_op(self):
        return self.boolean_op == ConditionGroupAbstract.OR_OP

    def is_and_op(self):
        return self.boolean_op == ConditionGroupAbstract.AND_OP

    def set_to_or_op(self):
        self.boolean_op = ConditionGroupAbstract.OR_OP
        self.save()

    def set_to_and_op(self):
        self.boolean_op = ConditionGroupAbstract.AND_OP
        self.save()

    def passes(self):
        raise NotImplementedError('ConditionGroupAbstract subclasses must override passes()')

    def add_has_value_condition(self, key_dict) -> ConditionAbstract:
        raise NotImplementedError('ConditionGroupAbstract subclasses must override add_boolean_condition()')

    def add_boolean_condition(self, key_dict) -> ConditionAbstract:
        raise NotImplementedError('ConditionGroupAbstract subclasses must override add_boolean_condition()')

    def add_comparison_condition(self, key_dict_1, key_dict_2, comparison) -> ConditionAbstract:
        raise NotImplementedError('ConditionGroupAbstract subclasses must override add_comparison_condition()')


class StateMachineAbstract(models.Model):
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

    def transit(self, state: State, reason: str):
        raise NotImplementedError('StateMachineAbstract subclasses must override transit()')


class RuleLibrary(ABC):
    """
    RuleLibraries help map a State's Rules to methods that alter the Game.
    """

    @staticmethod
    @abstractmethod
    def method_map(rule: str):
        """
        :param rule: str
        :return:
        """
        pass


class GameAbstract(models.Model):
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

    def update(self, rule_library: RuleLibrary):
        raise NotImplementedError('GameAbstract subclasses must override update()')

    def get_parameter(self, *args):
        raise NotImplementedError('GameAbstract subclasses must override get_parameter()')

    def get_parameter_value(self, *args):
        raise NotImplementedError('GameAbstract subclasses must override get_parameter_value()')

    def set_parameter_value(self, key, value):
        raise NotImplementedError('GameAbstract subclasses must override set_parameter_value()')

    def add_state_machine(self, state_slug: str, key_args):
        raise NotImplementedError('GameAbstract subclasses must override add_state_machine()')


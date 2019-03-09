from itertools import chain
from abc import ABC, abstractmethod

from django.db import models

from gamedefinitions.models import State, GameDefinition


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

    def get_rules(self):
        return self.current_state.rules

    def transit(self, state: State, reason: str):
        raise NotImplementedError('StateMachineAbstract subclasses must override transit()')


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

    def add_condition(self, condition_query_set: models.QuerySet):
        """
        :param condition_query_set: models.QuerySet
        :return:
        """
        self.condition_query_sets = list(chain(self.condition_query_sets, condition_query_set))

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

    def add_state_machine(self, state: State):
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

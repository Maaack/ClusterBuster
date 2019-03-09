from itertools import chain
from abc import ABC, abstractmethod

from django.db import models
from gamedefinitions.models import State


class StateMachineInterface(ABC):

    def __init__(self):
        self.root_state = None
        self.previous_state = None
        self.current_state = None

    @abstractmethod
    def get_state(self):
        pass

    @abstractmethod
    def set_state(self, state: State):
        pass

    @abstractmethod
    def get_rules(self):
        pass

    @abstractmethod
    def transit(self, state: State, reason: str):
        pass


class GameInterface(ABC):
    """
    RuleLibraries help map a State's Rules to methods that alter the Game.
    """

    def __init__(self):
        self.game_definition = None
        self.conditions = models.QuerySet()

    @abstractmethod
    def setup(self, game_definition_slug: str, *args, **kwargs):
        pass

    @abstractmethod
    def get_parameters(self):
        pass

    @abstractmethod
    def get_state_machines(self):
        pass

    @abstractmethod
    def add_parameter(self, key, value):
        """
        Adds a Parameter to the Game object.
        :param key:
        :param value:
        :return:
        """
        pass

    @abstractmethod
    def add_state_machine(self, state: State):
        """
        Adds a StateMachine to the Game object.
        :param state: State
        :return:
        """
        pass

    @abstractmethod
    def add_condition(self, conditions: models.QuerySet):
        """
        :param conditions: models.QuerySet
        :return:
        """
        self.conditions = list(chain(self.conditions, conditions))


class RuleLibrary(ABC):
    """
    RuleLibraries help map a State's Rules to methods that alter the Game.
    """

    @staticmethod
    @abstractmethod
    def evaluate(state_machine: StateMachineInterface, game: GameInterface):
        """
        :param state_machine: StateMachineInterface
        :param game: GameInterface
        :return:
        """
        pass
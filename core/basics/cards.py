import random
from abc import ABC, abstractmethod
from .generic import ObjectList


class Card(object):
    all = []

    def __init__(self, value=None):
        self.value = value if value else ""
        self.id = len(self.all) + 1
        self.all.append(self)

    def __eq__(self, other):
        if type(other) is not Card:
            return False
        return self.value == other.value

    def __str__(self):
        return "Card " + str(self.id)

    def __repr__(self):
        return 'Card({!r})'.format(self.value)


class CardStack(ObjectList):
    def __init__(self):
        super(CardStack, self).__init__(Card)


class Deck(CardStack):
    all = []

    def __init__(self):
        self.id = len(self.all) + 1
        self.all.append(self)
        super(Deck, self).__init__()

    def shuffle(self):
        random.shuffle(self)

    def draw(self, number=1):
        number = min(number, len(self))
        if number <= 0:
            return
        if number == 1:
            return self.pop()
        elif number >1:
            cards = CardStack()
            for i in range(number):
                cards.append(self.pop())
            return cards


class AbstractDeckParameters(ABC):
    def __init__(self):
        self.parameters = {}
        self.set_default_parameters()

    def __getattr__(self, item):
        try:
            return self.parameters[item]
        except KeyError:
            pass
        raise AttributeError

    @abstractmethod
    def set_default_parameters(self):
        pass


class AbstractDeckBuilder(ABC):
    @staticmethod
    @abstractmethod
    def build_deck(parameters=None):
        pass


class PatternDeckParameters(AbstractDeckParameters):
    def set_default_parameters(self):
        self.parameters['options'] = [1, 2, 3, 4]
        self.parameters['spots'] = 3


class PatternDeckBuilder(AbstractDeckBuilder):
    @staticmethod
    def build_deck(parameters=None):
        if parameters is None:
            parameters = PatternDeckParameters()
        return PatternDeckBuilder.__build_pattern_deck(parameters.options, parameters.spots, [])

    @staticmethod
    def __build_pattern_deck(options, open_spots, card_values=None):
        """
        @type options: list
        @type open_spots: number
        @type card_values: list
        """
        if card_values is None:
            card_values = []
        deck = Deck()
        if open_spots > 0 and len(options) > 0:
            for option in options:
                new_card_values = card_values.copy()
                new_card_values.append(option)
                remaining_options = options.copy()
                remaining_spots = open_spots - 1
                try:
                    remaining_options.remove(option)
                except ValueError:
                    continue
                deck.extend(PatternDeckBuilder.__build_pattern_deck(remaining_options, remaining_spots, new_card_values))
        else:
            card = Card(card_values)
            deck.append(card)
        return deck

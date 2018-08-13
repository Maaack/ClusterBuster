class Card(object):
    all = []

    def __init__(self, value):
        self.value = value
        self.id = len(self.all) + 1
        self.all.append(self)

    def __eq__(self, other):
        if type(other) is not Card:
            return False
        return self.value == other.value

    def __str__(self):
        return "Card " + str(self.id)


class CardDeck(object):
    all = []

    def __init__(self):
        self.id = len(self.all) + 1
        self.all.append(self)
        self.cards = []

    def create_deck(self):
        # TODO: Replace with passed in deck parameters
        self.cards = self.__create_card_list([1, 2, 3, 4], 3, [])

    def subtract_cards(self, subtract_cards):
        for subtract_card in subtract_cards:
            self.cards.remove(subtract_card)

    # TODO: Move into a CardDeckBuilder
    @staticmethod
    def __create_card_list(options, open_spots, card_values=None):
        """
        @type options: list
        @type open_spots: number
        @type card_values: list
        """
        if card_values is None:
            card_values = []
        cards_list = []
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
                cards_list.extend(CardDeck.__create_card_list(remaining_options, remaining_spots, new_card_values))
        else:
            card = Card(card_values)
            cards_list.append(card)
        return cards_list

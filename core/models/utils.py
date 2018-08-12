class Card(object):
    values = []

    def __init__(self, values):
        self.values = values


def create_card_list(options, open_spots, card_values):
    """
    @type options: list
    @type open_spots: number
    @type card_values: list
    """
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

            cards_list.extend(create_card_list(remaining_options, remaining_spots, new_card_values))
    else:
        card = Card(card_values)
        cards_list.append(card)
    return cards_list

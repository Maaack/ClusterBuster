from clusterbuster.mixins import ChoiceEnum


class GameStages(ChoiceEnum):
    CLOSED = 0
    OPEN = 1
    PLAYING = 2
    PAUSED = 3
    DONE = 4


class RoundStages(ChoiceEnum):
    COMPOSING = 0
    GUESSING = 1
    SCORING = 2
    DONE = 3


class PartyRoundStages(ChoiceEnum):
    ACTIVE = 0
    INACTIVE = 1
    WAITING = 2
    DONE = 3
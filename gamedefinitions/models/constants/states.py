from clusterbuster.mixins import ChoiceEnum


class GameStates(ChoiceEnum):
    INIT = "game_init"
    PLAY = "game_play"
    OVER = "game_over"


class GameStageStates(ChoiceEnum):
    DRAW_WORDS = "draw_words_stage"
    ROUNDS = "rounds_stage"


class RoundStates(ChoiceEnum):
    FIRST = "first_round"
    MIDDLE = "middle_rounds"
    LAST = "last_round"


class RoundStageStates(ChoiceEnum):
    SELECT_LEADER = "select_leader_stage"
    DRAW_CODE_CARD = "draw_code_card_stage"
    LEADERS_MAKE_HINTS = "leaders_make_hints_stage"
    TEAMS_SHARE_HINTS = "teams_share_hints_stage"
    PLAYERS_GUESS_CODES = "players_guess_codes_stage"
    TEAMS_SHARE_GUESSES = "teams_share_guesses_stage"
    SCORE_TEAMS = "score_teams_stage"


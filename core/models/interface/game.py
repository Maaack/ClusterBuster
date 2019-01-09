from typing import Optional
from django.db.models import Count
from core.models import Game, GameRoom, Player, Team
from core.constants import GAME_TEAM_LIMIT, GAME_ROUND_LIMIT, TEAM_PLAYER_LIMIT, TEAM_WORD_LIMIT, GAME_ROOM_CODE_LENGTH


class GameInterface(object):

    TEAM_NAMES = ['RED', 'BLUE', 'GREEN', 'YELLOW', 'MAGENTA']

    def __init__(self, game: Game):
        if not isinstance(game, Game):
            raise ValueError('`game` is not instance of Game')
        self.game = game

    def __get_teams_count(self):
        return self.game.teams.count()

    def __is_last_round(self):
        return self.get_current_round_number() >= GAME_ROUND_LIMIT

    def next_round(self):
        if not self.__is_last_round():
            self.game.rounds.create(number=self.get_current_round_number() + 1)

    def get_current_round_number(self):
        if self.game.current_round is not None:
            return self.game.current_round.number
        else:
            return 0

    def add_team(self, team=None):
        if team is not None and not isinstance(team, Team):
            raise ValueError('`team` is not instance of Team or None')
        elif team is not None:
            self.game.teams.add(team)
        else:
            self.game.teams.create()

    def fill_teams(self):
        teams_count = self.__get_teams_count()
        teams_left = GAME_TEAM_LIMIT - teams_count
        for i in range(teams_left):
            team_i = teams_count + i
            self.game.teams.create(name=GameInterface.TEAM_NAMES[team_i])

    def setup_room(self):
        try:
            return self.game.room
        except GameRoom.DoesNotExist:
            return GameRoom(game=self.game).save()

    def setup(self):
        self.fill_teams()
        self.setup_room()

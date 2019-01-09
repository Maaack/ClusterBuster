from typing import Optional
from django.db.models import Count
from core.models import Game, Player, Team
from core.constants import GAME_TEAM_LIMIT, GAME_ROUND_LIMIT, TEAM_PLAYER_LIMIT, TEAM_WORD_LIMIT, GAME_ROOM_CODE_LENGTH


class PlayerGameInterface(object):
    def __init__(self, player: Player, game: Game):
        if not isinstance(player, Player):
            raise ValueError('`player` is not of type Player')
        if not isinstance(game, Game):
            raise ValueError('`game` is not of type Game')
        self.player = player
        self.game = game

    def __get_teams_with_player_counts(self):
        return self.game.teams.annotate(num_players=Count('players')).order_by('num_players')

    def __get_team_with_fewest_players(self):
        return self.__get_teams_with_player_counts()[0]

    def has_player(self):
        return self.game.players.filter(pk=self.player.pk).exists()

    def get_team(self) -> Optional[Team]:
        if self.has_player():
            return self.game.teams.filter(players=self.player).first()
        return None

    def can_join(self):
        return not self.has_player()

    def get_default_team(self):
        return self.__get_team_with_fewest_players()

    def join_team(self, team: Team):
        if not isinstance(team, Team):
            raise ValueError('`team` is not of type Team')
        return PlayerTeamInterface(self.player, team).join()

    def join(self, team=None):
        if team is not None and not isinstance(team, Team):
            raise ValueError('`team` is not of type Team or None')

        if self.can_join():
            self.game.players.add(self.player)

            if team is not None:
                team = self.get_default_team()
            return self.join_team(team)
        return False


class PlayerTeamInterface(object):
    def __init__(self, player: Player, team: Team):
        if not isinstance(player, Player):
            raise ValueError('`player` is not of type Player')
        if not isinstance(team, Team):
            raise ValueError('`team` is not of type Team')
        self.player = player
        self.team = team

    def has_player(self):
        return self.team.players.filter(pk=self.player.pk).exists()

    def has_max_players(self):
        return self.team.players.count() >= TEAM_PLAYER_LIMIT

    def can_join(self):
        return not self.has_max_players() and not self.has_player()

    def join(self):
        if self.can_join():
            self.team.players.add(self.player)
            return True
        return False


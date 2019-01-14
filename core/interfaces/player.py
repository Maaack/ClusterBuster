from typing import Optional
from clusterbuster.mixins import interfaces

from core.models import Player, Team


class PlayerInterface(interfaces.ModelInterface):
    model = Player
    """
    Interface for players.
    """
    def __init__(self, player: Player):
        super(PlayerInterface, self).__init__(player)
        self.player = player


class TeamInterface(interfaces.ModelInterface):
    model = Team
    """
    Interface for teams.
    """
    def __init__(self, team: Team):
        super(TeamInterface, self).__init__(team)
        self.team = team


class Player2TeamInterface(interfaces.Model2ModelInterface):
    """
    Interface between players and teams.
    """
    PLAYER_LIMIT = 4
    model_a = Player
    model_b = Team

    def __init__(self, player: Player, team: Team):
        super(Player2TeamInterface, self).__init__(player, team)
        self.player = player
        self.team = team

    def has_player(self) -> bool:
        """
        Returns `True` if the player is in the team.
        :return: bool
        """
        return self.team.players.filter(pk=self.player.pk).exists()

    def has_max_players(self) -> bool:
        """
        Returns `True` if the team has the maximum number of players.
        :return: bool
        """
        return self.team.players.count() >= Player2TeamInterface.PLAYER_LIMIT

    def can_join(self) -> bool:
        """
        Returns `True` if the player can join the team.
        :return: bool
        """
        return not self.has_max_players() and not self.has_player()

    def join(self):
        """
        Attempts to join the player to the team.
        :return: None
        """
        if not self.can_join():
            raise Exception('Player can not join Team')
        self.team.players.add(self.player)
        self.team.save()

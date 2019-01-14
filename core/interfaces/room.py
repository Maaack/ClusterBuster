from typing import Optional

from django.db.models import Count

from clusterbuster.mixins import interfaces

from core.models import Player, Team, Room
from .player import Player2TeamInterface


class RoomInterface(interfaces.ModelInterface, interfaces.SetupInterface):
    model = Room
    """
    Interface for rooms.
    """
    TEAM_NAMES = ['RED', 'BLUE', 'GREEN', 'CYAN', 'MAGENTA', 'YELLOW']
    MIN_TEAMS_TO_START_GAME = 2

    def __init__(self, room: Room):
        super(RoomInterface, self).__init__(room)
        self.room = room

    def __get_teams_with_player_counts(self):
        return self.room.teams.annotate(num_players=Count('players')).order_by('num_players')

    def get_player_count(self):
        return self.room.players.count()

    def get_team_count(self):
        return self.room.teams.count()

    def is_filled(self):
        return self.get_team_count() == RoomInterface.MIN_TEAMS_TO_START_GAME

    def get_team_with_fewest_players(self):
        return self.__get_teams_with_player_counts().first()

    def get_minimum_players_per_team(self) -> int:
        team = self.get_team_with_fewest_players()
        if team is None:
            return 0
        return team.players.count()

    def add_team(self, team=None):
        if team is not None and not isinstance(team, Team):
            raise TypeError('`team` is not instance of Team or None')
        elif team is not None:
            self.room.teams.add(team)
        else:
            self.room.teams.create()

    def fill_teams(self):
        team_count = self.get_team_count()
        teams_left = RoomInterface.MIN_TEAMS_TO_START_GAME - team_count
        for i in range(teams_left):
            team_i = team_count + i
            team = Team(name=RoomInterface.TEAM_NAMES[team_i])
            team.save()
            self.room.teams.add(team)
        self.room.save()

    def get_first_teams(self, team_limit=1):
        team_count = self.get_team_count()
        if team_count < team_limit:
            raise Exception('Room must have at least %d first teams.' % team_limit)
        return self.room.teams.all()[0:team_limit]

    def is_setup(self):
        return self.is_filled()

    def setup(self):
        if self.is_setup():
            return
        self.fill_teams()


class Player2RoomInterface(interfaces.Model2ModelInterface):
    model_a = Player
    model_b = Room
    """
    Interface between players and rooms.
    """
    def __init__(self, player: Player, room: Room):
        super(Player2RoomInterface, self).__init__(player, room)
        self.player = player
        self.room = room

    def has_player(self) -> bool:
        """
        Returns `True` if the player is in the room.
        :return: bool
        """
        return bool(self.room.players.filter(pk=self.player.pk).exists())

    def is_leader(self) -> bool:
        """
        Returns `True` if the player is the room leader.
        :return: bool
        """
        return bool(self.room.session == self.player.session)

    def get_team(self) -> Optional[Team]:
        """
        Returns the player's team or None.
        :return: Optional[Team]
        """
        if self.has_player():
            return self.room.teams.filter(players=self.player).first()
        return None

    def get_opponent_team(self) -> Optional[Team]:
        """
        Returns the player's opponent's team or None.
        :return: Optional[Team]
        """
        if self.has_player():
            return self.room.teams.exclude(players=self.player).first()
        return None

    def can_join(self) -> bool:
        """
        Returns `True` if the player can join the room.
        :return: bool
        """
        return not self.has_player()

    def get_default_team(self) -> Team:
        """
        Returns the default team to join in the room.
        Will fill teams if there are none.
        :return: Team
        """
        room_interface = RoomInterface(self.room)
        if room_interface.get_team_count() <= 0:
            room_interface.fill_teams()
        return room_interface.get_team_with_fewest_players()

    def join_team(self, team: Team):
        """
        Attempts to join the player to a specific team in the room.
        Raises an exception if it fails.
        :raise: Exception
        :return: None
        """
        if not self.room.teams.filter(pk=team.pk).exists():
            raise Exception('Team does not exist in room.')
        Player2TeamInterface(self.player, team).join()

    def join(self, team=None):
        """
        Attempts to join the player to the room.
        Raises an exception if it fails.
        :raise: Exception
        :return: None
        """
        if not self.can_join():
            raise Exception('Player can not join room.')

        self.room.players.add(self.player)

        if team is None:
            team = self.get_default_team()
            if self.join_team(team):
                self.room.save()

from typing import Optional
from django.db.models import Count
from core.models import Room, Player, Game, Team , GameTeam
from core.constants import GAME_TEAM_LIMIT, GAME_ROUND_LIMIT, TEAM_PLAYER_LIMIT, TEAM_WORD_LIMIT


class PlayerInterface(object):
    def __init__(self, player: Player):
        if not isinstance(player, Player):
            raise TypeError('`player` is not of type Player')
        self.player = player

    def join_room(self, room: Room):
        PlayerRoomInterface(self.player, room).join()

    def join_team(self, team: Team):
        PlayerTeamInterface(self.player, team).join()


class PlayerTeamInterface(object):
    def __init__(self, player: Player, team: Team):
        if not isinstance(player, Player):
            raise TypeError('`player` is not instance of Player')
        if not isinstance(team, Team):
            raise TypeError('`team` is not instance of Team')
        self.player = player
        self.team = team

    def has_player(self):
        return self.team.players.filter(pk=self.player.pk).exists()

    def has_max_players(self):
        return self.team.players.count() >= TEAM_PLAYER_LIMIT

    def can_join(self):
        return not self.has_max_players() and not self.has_player()

    def join(self):
        if not self.can_join():
            raise Exception('Player can not join Team')
        self.team.players.add(self.player)
        self.team.save()


class RoomInterface(object):
    TEAM_NAMES = ['RED', 'BLUE', 'GREEN', 'CYAN', 'MAGENTA', 'YELLOW']
    MIN_PLAYERS_TO_START_GAME = 4
    MIN_TEAMS_TO_START_GAME = 2
    MIN_PLAYERS_PER_TEAM_TO_START_GAME = 2

    def __init__(self, room: Room):
        if not isinstance(room, Room):
            raise TypeError('`room` is not instance of Room')
        self.room = room

    def __get_teams_with_player_counts(self):
        return self.room.teams.annotate(num_players=Count('players')).order_by('num_players')

    def get_player_count(self):
        return self.room.players.count()

    def get_team_count(self):
        return self.room.teams.count()

    def get_team_with_fewest_players(self):
        return self.__get_teams_with_player_counts().first()

    def add_team(self, team=None):
        if team is not None and not isinstance(team, Team):
            raise TypeError('`team` is not instance of Team or None')
        elif team is not None:
            self.room.teams.add(team)
        else:
            self.room.teams.create()

    def fill_teams(self):
        team_count = self.get_team_count()
        teams_left = GAME_TEAM_LIMIT - team_count
        for i in range(teams_left):
            team_i = team_count + i
            team = Team(name=RoomInterface.TEAM_NAMES[team_i])
            team.save()
            self.room.teams.add(team)
        self.room.save()

    def setup(self):
        self.fill_teams()

    def can_start_game(self):
        team_count = self.get_team_count()
        player_count = self.get_player_count()
        teams_with_player_counts = self.__get_teams_with_player_counts()
        if team_count < RoomInterface.MIN_TEAMS_TO_START_GAME:
            return False
        if player_count < RoomInterface.MIN_PLAYERS_TO_START_GAME:
            return False
        for team in teams_with_player_counts:
            if team.num_players < RoomInterface.MIN_PLAYERS_PER_TEAM_TO_START_GAME:
                return False
        return True

    def start_game(self):
        if not self.can_start_game():
            raise Exception('Can not start game.')
        game = Game(room=self.room)
        game.save()
        RoomGameInterface(self.room, game).setup()
        GameInterface(game).setup()


class PlayerRoomInterface(object):
    """
    Interface between players and rooms.
    """
    def __init__(self, player: Player, room: Room):
        if not isinstance(player, Player):
            raise TypeError('`player` is not instance of Player')
        if not isinstance(room, Room):
            raise TypeError('`room` is not instance of Room')
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

    def join_team(self, team: Team) -> bool:
        """
        Attempts to join the player to a specific team in the room.
        Returns `True` if successful.
        :return: bool
        """
        if not self.room.teams.filter(pk=team.pk).exists():
            raise Exception('Team does not exist in room.')
        PlayerTeamInterface(self.player, team).join()

    def join(self, team=None) -> bool:
        """
        Attempts to join the player to the room.
        Raises an exception if it fails
        :return: None
        """
        if not self.can_join():
            raise Exception('Player can not join room.')

        self.room.players.add(self.player)

        if team is None:
            team = self.get_default_team()
            if self.join_team(team):
                self.room.save()



class RoomGameInterface(object):
    def __init__(self, room: Room, game: Game):
        if not isinstance(room, Room):
            raise TypeError('`room` is not instance of Room')
        if not isinstance(game, Game):
            raise TypeError('`game` is not instance of Game')
        self.room = room
        self.game = game

    def setup(self):
        team_count = RoomInterface(self.room).get_team_count()
        if team_count >= 2:
            two_teams = self.room.teams[0:2]
            self.game.teams.add(*two_teams)
        return False


class GameInterface(object):
    def __init__(self, game: Game):
        if not isinstance(game, Game):
            raise TypeError('`game` is not instance of Game')
        self.game = game

    def get_teams_count(self):
        return self.game.teams.count()

    def is_last_round(self):
        return self.get_current_round_number() >= GAME_ROUND_LIMIT

    def next_round(self):
        if not self.is_last_round():
            self.game.rounds.create(number=self.get_current_round_number() + 1)

    def get_current_round_number(self):
        if self.game.current_round is not None:
            return self.game.current_round.number
        else:
            return 0

    def setup(self):
        self.next_round()

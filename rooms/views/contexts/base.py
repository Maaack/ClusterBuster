from rooms.models import Player, Team, Room


class RoomContext:
    @staticmethod
    def load(room: Room) -> dict:
        """
        :param room: Room
        :return: dict
        """
        data = dict()
        data['room'] = room
        return data


class PlayerContext:
    @staticmethod
    def load(player: Player) -> dict:
        """
        :param player: Player
        :return: dict
        """
        data = dict()
        data['player'] = player
        data['is_player'] = True
        return data


class TeamContext:
    @staticmethod
    def load(team: Team) -> dict:
        """
        :param team: Team
        :return: dict
        """
        data = dict()
        data['team'] = team
        return data


class Player2RoomContext:
    @staticmethod
    def load(player: Player, room: Room):
        """
        :param player: Player
        :param room: Room
        :return: dict
        """
        data = dict()
        has_player = room.has_player(player)
        data['has_player'] = has_player
        data['can_join'] = room.can_join(player)
        if has_player:
            data['is_leader'] = room.is_leader(player)
        return data


class Player2TeamContext:
    @staticmethod
    def load(player: Player, team: Team):
        """
        :param player: Player
        :param team: Team
        :return: dict
        """
        data = dict()
        has_player = team.has_player(player)
        data['has_player'] = team.has_player(player)
        data['can_join'] = team.can_join(player)
        if has_player:
            data['is_leader'] = team.is_leader(player)
        return data

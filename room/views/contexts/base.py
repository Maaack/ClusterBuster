from room.models import Player, Group, Room


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


class GroupContext:
    @staticmethod
    def load(group: Group) -> dict:
        """
        :param group: Group
        :return: dict
        """
        data = dict()
        data['group'] = group
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


class Player2GroupContext:
    @staticmethod
    def load(player: Player, group: Group):
        """
        :param player: Player
        :param group: Group
        :return: dict
        """
        data = dict()
        has_player = group.has_player(player)
        data['has_player'] = group.has_player(player)
        data['can_join'] = group.can_join(player)
        if has_player:
            data['is_leader'] = group.is_leader(player)
        return data

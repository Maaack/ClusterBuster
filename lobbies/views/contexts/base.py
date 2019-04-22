from lobbies.models import Player, Team, Lobby


class LobbyContext:
    @staticmethod
    def load(lobby: Lobby) -> dict:
        """
        :param lobby: Lobby
        :return: dict
        """
        data = dict()
        data['lobby'] = lobby
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
        data['is_player'] = False
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


class Player2LobbyContext:
    @staticmethod
    def load(player: Player, lobby: Lobby):
        """
        :param player: Player
        :param lobby: Lobby
        :return: dict
        """
        data = dict()
        has_player = lobby.has_player(player)
        data['has_player'] = has_player
        data['can_join'] = lobby.can_join(player)
        if has_player:
            data['is_leader'] = lobby.is_leader(player)
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

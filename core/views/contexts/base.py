from core.interfaces import PlayerGameInterface, RoomInterface, PlayerRoomInterface
from core.models import Player, Room


class RoomContext():
    @staticmethod
    def load(room):
        data = dict()
        data['player'] = None
        data['is_player'] = False
        data['is_leader'] = False
        data['has_player'] = False
        return data


class PlayerRoomContext:
    @staticmethod
    def load(player, room):
        """
        :param player: Player
        :param room: Room
        :return: dict
        """
        data = dict()
        player_room_interface = PlayerRoomInterface(player, room)
        data['player'] = player
        data['is_player'] = True
        data['is_leader'] = player_room_interface.is_leader()
        data['has_player'] = player_room_interface.has_player()
        data['can_join'] = player_room_interface.can_join()
        data['player_team'] = player_room_interface.get_team()
        data['opponent_team'] = player_room_interface.get_opponent_team()
        if data['is_leader']:
            room_interface = RoomInterface(room)
            data['can_start_game'] = room_interface.can_start_game()
        return data


class ContextDataLoader(object):
    @staticmethod
    def get_game_data(game):
        """
        :param game: Game
        :return: dict
        """
        data = dict()
        data['game'] = game
        data['round'] = game.current_round
        return data

    @staticmethod
    def get_player_data(player, game):
        """
        :param player: Player
        :param game: Game
        :return: dict
        """
        player_game_interface = PlayerGameInterface(player, game)
        data = dict()
        data['player'] = player
        has_player = player_game_interface.has_player()
        team = player_game_interface.get_team()
        data['player_in_game'] = has_player
        data['player_team'] = team
        data['player_team_round'] = None
        data['player_team_round_leader'] = None
        data['is_leader'] = None
        if has_player and team and team.current_team_round:
            team_round = team.current_team_round
            round_leader = team.current_team_round.leader
            is_leader = round_leader == player
            data['player_team_round'] = team_round
            data['player_team_round_leader'] = round_leader
            data['is_leader'] = is_leader
            data.update(ContextDataLoader.get_round_hints_data(game.teams.all(), team))
            if is_leader:
                data.update(ContextDataLoader.get_round_leader_word_data(team_round))
        return data

    @staticmethod
    def get_round_hints_data(teams, player_team):
        """
        :param team_round: TeamRound
        :return: dict
        """
        data = dict()
        for team in teams:
            target_words = team.current_team_round.target_words.order_by('order').all()
            target_words_dict = [
                {'hint': target_word.get_hint_text(), 'order': target_word.order + 1} for
                target_word in target_words]
            if team == player_team:
                data['team_hints'] = target_words_dict
            else:
                data['opponent_team_hints'] = target_words_dict
        return data

    @staticmethod
    def get_round_leader_word_data(team_round):
        """
        :param team_round: TeamRound
        :return: dict
        """
        data = dict()
        target_words = team_round.target_words.all()
        data['words'] = [
            {'text': target_word.team_word.word.text, 'position': target_word.team_word.position} for
            target_word in target_words]
        return data

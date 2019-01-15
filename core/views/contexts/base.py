from core import interfaces
from core.models import Player, Room


class RoomContext:
    @staticmethod
    def load(room):
        data = dict()
        # Set by the RoomDetail view.
        # data['room'] = room
        interface = interfaces.RoomGamesInterface(room)
        if interface.has_game():
            game = interface.get_current_game()
            game_data = GameContext.load(game)
            data.update(game_data)
        return data


class GameContext:
    @staticmethod
    def load(game):
        """
        :param game: Game
        :return: dict
        """
        data = dict()
        data['game'] = game
        interface = interfaces.GameRoundsInterface(game)
        game_is_started = interface.is_started()
        data['game_is_started'] = game_is_started
        if game_is_started:
            current_round = interface.get_current_round()
            round_data = RoundContext.load(current_round)
            data.update(round_data)
        return data


class RoundContext:
    @staticmethod
    def load(round_obj):
        """
        :param round_obj: Round
        :return: dict
        """
        data = dict()
        data['round'] = round_obj
        interface = interfaces.RoundInterface(round_obj)
        data['round_stage_name'] = interface.get_current_stage_name()
        data['round_is_composing'] = interface.is_composing()
        data['round_is_guessing'] = interface.is_guessing()
        data['round_is_done'] = interface.is_done()
        return data


class Player2RoomContext:
    @staticmethod
    def load(player, room):
        """
        :param player: Player
        :param room: Room
        :return: dict
        """
        data = dict()
        player_room_interface = interfaces.Player2RoomInterface(player, room)
        room_interface = interfaces.RoomGamesInterface(room)
        data['player'] = player
        data['is_player'] = True
        is_room_leader = player_room_interface.is_leader()
        data['is_room_leader'] = is_room_leader
        data['room_has_player'] = player_room_interface.has_player()
        data['can_join'] = player_room_interface.can_join()
        data['player_team'] = player_room_interface.get_team()
        data['opponent_team'] = player_room_interface.get_opponent_team()
        if is_room_leader:
            data['can_start_game'] = room_interface.can_start_game()
        if not room_interface.has_game():
            return data
        game = room_interface.get_current_game()
        player_2_game_data = Player2GameContext.load(player, game)
        data.update(player_2_game_data)
        return data


class Player2GameContext:
    @staticmethod
    def load(player, game):
        """
        :param player: Player
        :param game: Game
        :return: dict
        """
        data = dict()
        player_2_game_interface = interfaces.Player2GameInterface(player, game)
        game_has_player = player_2_game_interface.has_player()
        data['game_has_player'] = game_has_player
        if not game_has_player:
            return data
        player_party = player_2_game_interface.get_party()
        opponent_party = player_2_game_interface.get_opponent_party()
        data['player_party'] = player_party
        data['opponent_party'] = opponent_party
        game_interface = interfaces.GameRoundsInterface(game)
        if not game_interface.is_started():
            return data
        player_party_round = player_party.current_party_round
        opponent_party_round = opponent_party.current_party_round
        data['player_party_round'] = player_party_round
        data['opponent_party_round'] = opponent_party_round
        data['player_party_round_context'] = Player2PartyRoundContext.load(player, player_party_round)
        data['opponent_party_round_context'] = Player2PartyRoundContext.load(player, opponent_party_round)
        data['player_party_round_hints'] = PartyRoundHintsContext.load(player_party_round)
        data['opponent_party_round_hints'] = PartyRoundHintsContext.load(opponent_party_round)
        return data


class Player2PartyRoundContext:
    @staticmethod
    def load(player, party_round):
        """
        :param player: Player
        :param party_round: PartyRound
        :return: dict
        """
        data = dict()
        party_round_interface = interfaces.PartyRoundInterface(party_round)
        data['is_waiting'] = party_round_interface.is_waiting()
        data['is_done'] = party_round_interface.is_done()
        data['guessing_players'] = party_round_interface.get_non_leader_players()
        player_2_party_round_interface = interfaces.Player2PartyRoundInterface(player, party_round)
        data['is_round_leader'] = player_2_party_round_interface.is_leader()
        party_round_guesses_interface = interfaces.PartyRoundGuessesInterface(party_round)
        data['conflicting_guesses'] = party_round_guesses_interface.get_target_words_with_conflicting_guesses()
        return data


class PartyRoundHintsContext:
    @staticmethod
    def load(party_round):
        """
        :param party_round: PartyRound
        :return: dict
        """
        interface = interfaces.PartyRoundGuessesInterface(party_round)
        target_words = interface.get_target_word_distinct_guess_count().order_by('order').all()

        data = [
            {'hint': target_word.get_hint_text(),
             'order': target_word.order + 1,
             'conflicting_guesses': target_word.guesses > 1} for target_word in target_words]
        return data


class PartyRoundLeaderWordContext:
    @staticmethod
    def load(party_round):
        """
        :param party_round: PartyRound
        :return: dict
        """
        data = dict()
        target_words = party_round.target_words.all()
        data = [
            {'text': target_word.party_word.word.text,
             'position': target_word.party_word.position} for target_word in target_words]
        return data

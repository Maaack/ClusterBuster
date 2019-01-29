from typing import Optional

from django.db.models import Count, Sum

from clusterbuster.mixins import interfaces

from core.basics import PatternDeckBuilder, CardStack, Card
from core.models import Game, Player, Room, Party, Word, PartyWord
from .room import RoomInterface


class GameTypeInterface(object):
    GAME_TYPE_NAME = "ClusterBuster"

    def __init__(self):
        self.name = GameTypeInterface.GAME_TYPE_NAME


class RoomGamesInterface(RoomInterface):
    MIN_PLAYERS_TO_START_GAME = 4
    MIN_TEAMS_TO_START_GAME = 2
    MIN_PLAYERS_PER_TEAM_TO_START_GAME = 2

    def can_start_game(self):
        room_interface = RoomInterface(self.room)
        team_count = room_interface.get_team_count()
        player_count = room_interface.get_player_count()
        minimum_players_per_team = room_interface.get_minimum_players_per_team()
        if team_count < RoomGamesInterface.MIN_TEAMS_TO_START_GAME:
            return False
        if player_count < RoomGamesInterface.MIN_PLAYERS_TO_START_GAME:
            return False
        if minimum_players_per_team < RoomGamesInterface.MIN_PLAYERS_PER_TEAM_TO_START_GAME:
            return False
        return True

    def get_current_game(self):
        return self.room.current_game or self.room.games.last()

    def has_game(self):
        return self.get_current_game() is not None

    def start_game(self):
        if not self.can_start_game():
            raise Exception('Can not start game.')
        if not self.has_game():
            game = Game(room=self.room)
            game.save()
        else:
            game = self.get_current_game()
        Room2GameInterface(self.room, game).setup()
        GameInterface(game).setup()

    def is_setup(self):
        if not super(RoomGamesInterface, self).is_setup():
            return False
        if not self.has_game():
            return False
        current_game = self.get_current_game()
        if not GameInterface(current_game).is_setup():
            return False
        return True

    def setup(self):
        super(RoomGamesInterface, self).setup()
        if self.is_setup():
            return
        self.start_game()


class GameInterface(interfaces.ModelInterface, interfaces.SetupInterface):
    """
    Interface for games.
    """
    ROUND_LIMIT = 8
    PARTY_LIMIT = 2

    model = Game

    def __init__(self, game: Game):
        super(GameInterface, self).__init__(game)
        self.game = game

    def get_party_count(self):
        return self.game.parties.count()

    def is_game_filled(self):
        return self.get_party_count() == GameInterface.PARTY_LIMIT

    def is_setup(self):
        return self.is_game_filled()

    def setup(self):
        pass


class Player2GameInterface(interfaces.Model2ModelInterface):
    model_a = Player
    model_b = Game

    def __init__(self, player: Player, game: Game):
        super(Player2GameInterface, self).__init__(player, game)
        self.player = player
        self.game = game

    def has_player(self):
        return self.game.teams.filter(players=self.player).exists()

    def get_party(self) -> Optional[Party]:
        if self.has_player():
            return self.game.parties.filter(team__players=self.player).first()
        return None

    def get_opponent_party(self) -> Optional[Party]:
        if self.has_player():
            return self.game.parties.exclude(team__players=self.player).first()
        return None


class Room2GameInterface(interfaces.Model2ModelInterface, interfaces.SetupInterface):
    MIN_TEAMS_PER_GAME = 2

    model_a = Room
    model_b = Game

    def __init__(self, room: Room, game: Game):
        super(Room2GameInterface, self).__init__(room, game)
        self.room = room
        self.game = game

    def is_current_game(self):
        return self.room.current_game == self.game

    def set_current_game(self):
        self.room.current_game = self.game
        self.room.save()

    def create_parties_for_teams(self, teams):
        for team in teams:
            party = Party.objects.create(game=self.game, team=team)
            PartyInterface(party).setup()

    def is_setup(self):
        if not self.is_current_game():
            return False
        if not GameInterface(self.game).is_game_filled():
            return False
        return True

    def setup(self):
        if self.is_setup():
            return
        game_interface = GameInterface(self.game)
        if not game_interface.is_game_filled():
            party_limit = GameInterface.PARTY_LIMIT
            room_interface = RoomInterface(self.room)
            teams = room_interface.get_first_teams(party_limit)
            self.create_parties_for_teams(teams)
        if not self.is_current_game():
            self.set_current_game()


class Player2PartyInterface(interfaces.Model2ModelInterface):
    model_a = Player
    model_b = Party

    def __init__(self, player: Player, party: Party):
        super(Player2PartyInterface, self).__init__(player, party)
        self.player = player
        self.party = party

    def has_player(self):
        return self.party.team.players.filter(pk=self.player.pk).exists()


class PartyInterface(interfaces.ModelInterface, interfaces.SetupInterface):
    PARTY_WORD_COUNT = 4

    model = Party

    def __init__(self, party: Party):
        super(PartyInterface, self).__init__(party)
        self.party = party

    def get_word_count(self):
        return self.party.party_words.count()

    def has_words(self):
        return self.get_word_count() >= PartyInterface.PARTY_WORD_COUNT

    def set_words(self):
        if self.has_words():
            return
        word_count_goal = PartyInterface.PARTY_WORD_COUNT
        word_count = self.get_word_count()
        add_words = word_count_goal - word_count
        if add_words > 0:
            # TODO: Pick random words for all parties simultaneously.
            # TODO: Replace the call below with more performant one.
            # This can be slow depending on the database backend.
            random_words = Word.objects.order_by('?').all()[:add_words]
            for i, random_word in enumerate(random_words):
                new_position = i+1
                party_word = PartyWord(party=self.party, word=random_word, position=new_position)
                party_word.save()
                # This doesn't exist
                # PartyWordInterface(party_word).setup()

    def draw_card(self):
        deck = PatternDeckBuilder.build_deck()
        drawn_cards = self.get_drawn_cards()
        deck.reduce(drawn_cards)
        deck.shuffle()
        return deck.draw()

    def get_drawn_cards(self):
        cards = CardStack()
        for team_round in self.party.party_rounds.order_by('round__number').all():
            target_words = team_round.target_words.order_by('order').all()
            card_values = [target_word.team_word.position for target_word in target_words]
            if len(card_values) > 0:
                cards.append(Card(card_values))
        return cards

    def is_setup(self):
        return self.has_words()

    def setup(self):
        if self.is_setup():
            return
        self.set_words()

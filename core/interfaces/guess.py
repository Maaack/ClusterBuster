from django.db.models import Count

from clusterbuster.mixins import interfaces

from core.models import Player, Round, PartyRound, PlayerGuess
from . import PartyRoundInterface, RoundInterface, Player2PartyRoundInterface


class PlayerGuessInterface(interfaces.ModelInterface):
    model = PlayerGuess

    def __init__(self, player_guess):
        super(PlayerGuessInterface, self).__init__(player_guess)
        self.player_guess = player_guess

    def is_valid(self):
        if self.player_guess.guess is None:
            return False
        if len(self.player_guess.guess) == 0:
            return False
        return True


class RoundGuessesInterface(RoundInterface):
    model = Round

    def __init__(self, round_obj):
        super(RoundGuessesInterface, self).__init__(round_obj)
        self.round = round_obj

    def get_party_rounds(self):
        return self.round.party_rounds

    def get_parties(self):
        return self.round.game.parties

    def set_guesses(self):
        all_players = self.get_players().all()
        party_rounds = self.get_party_rounds().all()
        for party_round in party_rounds:
            for player in all_players:
                Player2PartyRoundGuessesInterface(player, party_round).setup()

    def has_party_round_guesses(self):
        party_rounds = self.round.party_rounds.all()
        for party_round in party_rounds:
            if not PartyRoundGuessesInterface(party_round).is_setup():
                return False
        return True

    def is_setup(self):
        if not super(RoundGuessesInterface, self).is_setup():
            return False
        if not self.has_party_round_guesses():
            return False
        return True

    def setup(self):
        if self.is_setup():
            return
        super(RoundGuessesInterface, self).setup()
        self.set_guesses()


class Player2PartyRoundGuessesInterface(Player2PartyRoundInterface, interfaces.SetupInterface):
    model_a = Player
    model_b = PartyRound

    def __init__(self, player, party_round):
        super(Player2PartyRoundGuessesInterface, self).__init__(player, party_round)
        self.player = player
        self.party_round = party_round

    def get_guesses(self):
        return PlayerGuess.objects.filter(player=self.player, target_word__party_round=self.party_round)

    def has_guesses(self):
        return self.get_guesses().exists()

    def set_guesses(self):
        target_words = PartyRoundGuessesInterface(self.party_round).get_target_words().all()
        for target_word in target_words:
            PlayerGuess.objects.get_or_create(player=self.player, target_word=target_word)

    def is_setup(self):
        if not self.has_guesses():
            return False
        return True

    def setup(self):
        if self.is_setup():
            return
        self.set_guesses()


class PartyRoundGuessesInterface(PartyRoundInterface):
    def __get_player_guesses_by_target_word(self):
        return self.party_round.target_words.values('pk', 'player_guesses__player', 'player_guesses__guess')

    def __set_team_guess_to_first_guess(self):
        valid_guesses = self.get_valid_guesses()
        target_word_guesses = self.__get_player_guesses_by_target_word()
        # TODO: Continue working here
        print(target_word_guesses)

    def get_target_word_distinct_guess_count(self):
        return self.party_round.target_words.annotate(guesses=Count('player_guesses__guess', distinct=True))

    def get_guessing_players(self):
        return self.get_non_leader_players()

    def get_guesses(self):
        guessing_players = self.get_guessing_players()
        return PlayerGuess.objects.filter(
            player__in=guessing_players,
            target_word__party_round=self.party_round
        )

    def get_valid_guesses(self):
        return self.get_guesses().exclude(guess=None)

    def get_missing_guesses(self):
        return self.get_guesses().filter(guess=None)

    def get_expected_guess_count(self):
        target_words_count = self.party_round.target_words.count()
        guesser_count = self.get_guessing_players().count()
        return guesser_count * target_words_count

    def get_guess_count(self):
        return self.get_guesses().count()

    def get_valid_guess_count(self):
        return self.get_valid_guesses().count()

    def get_target_words_with_conflicting_guesses(self):
        return self.get_target_word_distinct_guess_count().filter(guesses__gt=1)

    def get_conflicting_guesses_count(self):
        return self.get_target_words_with_conflicting_guesses().count()

    def can_set_party_guess(self):
        expected_guess_count = self.get_expected_guess_count()
        valid_guess_count = self.get_valid_guess_count()
        if expected_guess_count != valid_guess_count:
            return False
        conflicting_guesses_count = self.get_conflicting_guesses_count()
        print("Conflicting Guesses")
        print(conflicting_guesses_count)
        if conflicting_guesses_count > 0:
            return False
        self.__set_team_guess_to_first_guess()
        return False

    def set_party_guess(self):
        """
        Tries to create a Team Guess out of Player Guesses
        """
        if not self.can_set_party_guess():
            raise Exception('Can not set team guess.')
        return

    def has_guesses(self):
        return self.get_guess_count() == self.get_expected_guess_count()

    def is_setup(self):
        if not super(PartyRoundGuessesInterface, self).is_setup():
            return False
        if not self.has_guesses():
            return False
        return True

    def setup(self):
        if self.is_setup():
            return
        super(PartyRoundGuessesInterface, self).setup()
        self.set_guesses()

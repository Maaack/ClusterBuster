from clusterbuster.mixins import interfaces

from core.models import Player, Round, PartyRound, TargetWord, choices
from . import PartyInterface
from .game import GameInterface


class RoundInterface(interfaces.ModelInterface, interfaces.SetupInterface):
    model = Round

    def __init__(self, round_obj: Round):
        super(RoundInterface, self).__init__(round_obj)
        self.round = round_obj

    def __advance_stage(self):
        if not self.is_done():
            self.round.stage += 1
            self.round.save()

    def get_current_stage_name(self):
        return choices.RoundStages.choice(self.round.stage)

    def get_party_rounds(self):
        return self.round.party_rounds

    def get_parties(self):
        return self.round.game.parties

    def has_party_rounds(self):
        return self.get_party_rounds().count() == self.get_parties().count()

    def set_party_rounds(self):
        if self.has_party_rounds():
            return
        for party in self.round.game.parties.all():
            party_round = PartyRound(party=party, round=self.round)
            party_round.save()
            PartyRoundInterface(party_round).setup()

    def set_as_current_round(self):
        self.round.game.current_round = self.round
        self.round.game.save()

    def advance_if_all_parties_waiting(self):
        parties = self.round.game.parties
        all_parties_count = parties.count()
        waiting_parties_count = parties.filter(current_party_round__stage=choices.PartyRoundStages.WAITING.value).count()
        if all_parties_count == waiting_parties_count:
            self.round.party_rounds.update(stage=choices.PartyRoundStages.DONE.value)

    def advance_stage(self):
        parties = self.round.game.parties
        all_parties_count = parties.count()
        done_parties_count = parties.filter(current_party_round__stage=choices.PartyRoundStages.DONE.value).count()
        if all_parties_count == done_parties_count:
            self.__advance_stage()

    def is_composing(self):
        return self.round.stage == choices.RoundStages.COMPOSING.value

    def is_guessing(self):
        return self.round.stage == choices.RoundStages.GUESSING.value

    def is_done(self):
        return self.round.stage == choices.RoundStages.DONE.value

    def is_setup(self):
        if not self.has_party_rounds():
            return False
        if self.round.stage is None:
            return False
        return True

    def setup(self):
        if self.is_setup():
            return
        self.set_party_rounds()
        self.set_as_current_round()


class GameRoundsInterface(GameInterface):
    """
    Interface for games with rounds.
    """
    ROUND_LIMIT = 8

    def is_started(self):
        return self.get_current_round_number() > 0

    def is_first_round(self):
        return self.get_current_round_number() == 1

    def is_last_round(self):
        return self.get_current_round_number() >= GameRoundsInterface.ROUND_LIMIT

    def get_current_round(self):
        return self.game.current_round or None

    def get_current_round_number(self):
        current_round = self.get_current_round()
        if current_round is not None:
            return current_round.number
        else:
            return 0

    def next_round(self):
        if not self.is_last_round():
            next_round_number = self.get_current_round_number() + 1
            round_obj = Round(game=self.game, number=next_round_number)
            round_obj.save()
            RoundInterface(round_obj).setup()

    def is_setup(self):
        if not super(GameRoundsInterface, self).is_setup():
            return False
        if not self.is_started():
            return False
        return True

    def setup(self):
        super(GameRoundsInterface, self).setup()
        if self.is_setup():
            return
        self.next_round()


class PartyRoundInterface(interfaces.ModelInterface, interfaces.SetupInterface):
    """
    Interface for party rounds.
    """
    model = PartyRound

    def __init__(self, party_round: PartyRound):
        super(PartyRoundInterface, self).__init__(party_round)
        self.party_round = party_round

    def get_current_stage_name(self):
        return choices.PartyRoundStages.choice(self.party_round.stage)

    def advance_stage(self):
        if self.party_round.stage in (choices.PartyRoundStages.ACTIVE.value, choices.PartyRoundStages.INACTIVE.value):
            self.party_round.stage = choices.PartyRoundStages.WAITING.value
            self.party_round.save()
        RoundInterface(self.party_round.round).advance_if_all_parties_waiting()

    def reset_stage(self):
        self.party_round.stage = choices.PartyRoundStages.ACTIVE.value
        self.party_round.save()

    def is_waiting(self):
        return self.party_round.stage == choices.PartyRoundStages.WAITING.value

    def is_active(self):
        return self.party_round.stage == choices.PartyRoundStages.ACTIVE.value

    def is_done(self):
        return self.party_round.stage == choices.PartyRoundStages.DONE.value

    def set_as_current_round(self):
        self.party_round.party.current_party_round = self.party_round
        self.party_round.party.save()

    def is_leader(self, player):
        return self.party_round.leader == player

    def get_guessing_players(self):
        return self.party_round.party.team.players.exclude(id=self.party_round.leader.id)

    def set_leader(self):
        player_count = self.party_round.party.team.players.count()
        if player_count == 0:
            return
        offset = self.party_round.round.number % player_count
        player = self.party_round.party.team.players.all()[offset]
        Player2PartyRoundInterface(player, self.party_round).set_leader()

    def has_target_words(self):
        return self.party_round.target_words.count() > 0

    def get_party_word_at_position(self, position_int):
        return self.party_round.party.party_words.get(position=position_int)

    def set_target_words(self):
        if self.has_target_words():
            return
        party_interface = PartyInterface(self.party_round.party)
        card = party_interface.draw_card()
        for order, position in enumerate(card.value):
            party_word = self.get_party_word_at_position(position)
            target_word = TargetWord(party_round=self.party_round, party_word=party_word, order=order)
            target_word.save()

    def get_non_target_words(self):
        return self.party_round.party.party_words.exclude(
            target_words__in=self.party_round.target_words.all()
        ).all()

    def is_setup(self):
        return self.has_target_words()

    def setup(self):
        if self.party_round.leader is None:
            self.set_leader()
        self.set_target_words()
        self.set_as_current_round()


class Player2PartyRoundInterface(interfaces.Model2ModelInterface):
    model_a = Player
    model_b = PartyRound

    def __init__(self, player, party_round):
        super(Player2PartyRoundInterface, self).__init__(player, party_round)
        self.player = player
        self.party_round = party_round

    def is_leader(self):
        return self.party_round.leader == self.player

    def set_leader(self):
        self.party_round.leader = self.player
        self.party_round.save()
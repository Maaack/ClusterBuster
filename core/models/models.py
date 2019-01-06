import random
import string

from django.db import models
from django.db.models import Count
from django.utils.translation import ugettext_lazy as _

from clusterbuster.mixins.models import TimeStamped
from core.basics import PatternDeckBuilder, CardStack, Card
from core.constants import GAME_TEAM_LIMIT, GAME_ROUND_LIMIT, TEAM_PLAYER_LIMIT, TEAM_WORD_LIMIT, GAME_ROOM_CODE_LENGTH
from .managers import ActiveGameRoomManager, RandomWordManager
from .mixins import SessionOptional, GameRoomStages, RoundStages, TeamRoundStages


# Create your models here.
class Player(TimeStamped, SessionOptional):
    class Meta:
        verbose_name = _("Player")
        verbose_name_plural = _("Players")
        ordering = ["name", "-created"]

    name = models.CharField(_("Name"), max_length=24)

    def __str__(self):
        return str(self.name)

    def get_game_team(self, game):
        return Team.objects.get(game=game, players=self)


class Word(TimeStamped):
    class Meta:
        verbose_name = _("Word")
        verbose_name_plural = _("Words")
        ordering = ["text", "-created"]

    text = models.CharField(_("Text"), max_length=16, db_index=True)
    objects = RandomWordManager()

    def __str__(self):
        return str(self.text)


class Game(TimeStamped, SessionOptional):
    class Meta:
        verbose_name = _("Game")
        verbose_name_plural = _("Games")
        ordering = ["-created"]

    players = models.ManyToManyField(Player, blank=True)
    current_round = models.ForeignKey('Round', on_delete=models.SET_NULL, related_name="+", null=True, blank=True)

    def save(self, *args, **kwargs):
        super(Game, self).save(*args, **kwargs)
        self.create_teams()
        self.create_room()

    def create_teams(self, team_count=GAME_TEAM_LIMIT):
        current_team_count = self.teams.count()
        team_slots = GAME_TEAM_LIMIT - current_team_count
        if team_slots > 0:
            new_teams = min(team_slots, team_count)
            for team_number in range(new_teams):
                self.teams.create()

    def create_room(self):
        try:
            has_room = self.gameroom is not None
        except GameRoom.DoesNotExist:
            GameRoom(game=self).save()
            has_room = True
        return has_room

    def join(self, player):
        if type(player) is Player and not self.has_player(player):
            self.players.add(player)
            return self.get_team_with_fewest_players().join(player)
        return False

    def get_team_with_fewest_players(self):
        return self.get_teams_with_player_counts()[0]

    def get_teams_with_player_counts(self):
        self.create_teams()
        return self.teams.annotate(num_players=Count('players')).order_by('num_players')

    def has_player(self, player):
        return self.players.filter(pk=player.pk).exists()

    def get_player_team(self, player):
        if type(player) is Player and self.has_player(player):
            return self.teams.filter(players=player).first()
        return None

    def next_round(self):
        if not self.is_last_round():
            self.rounds.create(number=self.get_current_round_number() + 1)

    def get_current_round_number(self):
        if self.current_round:
            return self.current_round.number
        else:
            return 0

    def is_last_round(self):
        return self.get_current_round_number() >= GAME_ROUND_LIMIT


class GameRoom(TimeStamped):
    class Meta:
        verbose_name = _("Game Room")
        verbose_name_plural = _("Game Rooms")
        ordering = ["-created"]

    game = models.OneToOneField(Game, on_delete=models.CASCADE)
    code = models.SlugField(_("Code"), max_length=16)
    stage = models.PositiveSmallIntegerField(_("Stage"), default=GameRoomStages.OPEN.value,
                                             choices=GameRoomStages.choices())

    objects = models.Manager()
    active = ActiveGameRoomManager()

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        self.set_code()
        super(GameRoom, self).save(*args, **kwargs)

    def get_current_stage_name(self):
        return GameRoomStages.choice(self.stage)

    def get_current_round(self):
        return self.game.current_round

    def set_code(self):
        if not self.code:
            self.code = GameRoom.create_code()

    @staticmethod
    def create_code(length=GAME_ROOM_CODE_LENGTH):
        return ''.join(random.choice(string.ascii_uppercase) for _ in range(length))


class Team(TimeStamped):
    class Meta:
        verbose_name = _("Team")
        verbose_name_plural = _("Teams")
        ordering = ["-created"]

    players = models.ManyToManyField(Player, blank=True)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='teams')
    current_team_round = models.ForeignKey('TeamRound', on_delete=models.SET_NULL, related_name="+", null=True,
                                           blank=True)

    def save(self, *args, **kwargs):
        super(Team, self).save(*args, **kwargs)
        self.set_words()

    def join(self, player):
        if type(player) is Player and not self.has_max_players():
            self.players.add(player)
            return True
        return False

    def has_player(self, player):
        return self.players.filter(pk=player.pk).exists()

    def has_max_players(self):
        return self.players.count() >= TEAM_PLAYER_LIMIT

    def set_words(self):
        word_count = self.team_words.count()
        add_words = TEAM_WORD_LIMIT - word_count
        if add_words > 0:
            for i in range(word_count, TEAM_WORD_LIMIT):
                self.team_words.create(word=Word.objects.random(), game=self.game, position=i + 1)

    def draw_card(self):
        deck = PatternDeckBuilder.build_deck()
        drawn_cards = self.get_drawn_cards()
        deck.reduce(drawn_cards)
        deck.shuffle()
        return deck.draw()

    def get_drawn_cards(self):
        cards = CardStack()
        for team_round in self.team_rounds.order_by('round__number').all():
            team_round_words = team_round.team_round_words.order_by('order').all()
            card_values = [team_round_word.team_word.position for team_round_word in team_round_words]
            if len(card_values) > 0:
                cards.append(Card(card_values))
        return cards


class Round(TimeStamped):
    class Meta:
        verbose_name = _("Round")
        verbose_name_plural = _("Rounds")
        ordering = ["-created"]

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='rounds')
    number = models.PositiveSmallIntegerField(_("Round Number"), db_index=True)
    stage = models.PositiveSmallIntegerField(_("Stage"), default=RoundStages.COMPOSING.value,
                                             choices=RoundStages.choices())

    def __str__(self):
        return "Round " + str(self.number)

    def save(self, *args, **kwargs):
        super(Round, self).save(*args, **kwargs)
        self.set_team_rounds()
        self.set_as_current_round()

    def get_current_stage_name(self):
        return RoundStages.choice(self.stage)

    def set_team_rounds(self):
        if self.team_rounds.count() == 0:
            for team in self.game.teams.all():
                self.team_rounds.create(team=team)

    def set_as_current_round(self):
        self.game.current_round = self
        self.game.save()

    def update_all_team_stages(self):
        game_teams = self.game.teams
        all_teams_count = game_teams.count()
        waiting_teams_count = game_teams.filter(current_team_round__stage=TeamRoundStages.WAITING.value).count()
        if all_teams_count == waiting_teams_count:
            self.team_rounds.update(stage=TeamRoundStages.DONE.value)

    def advance_stage(self):
        game_teams = self.game.teams
        all_teams_count = game_teams.count()
        done_teams_count = game_teams.filter(current_team_round__stage=TeamRoundStages.DONE.value).count()
        if all_teams_count == done_teams_count:
            self.__advance_stage()

    def __advance_stage(self):
        if not self.is_done():
            self.stage += 1
            self.save()

    def is_composing(self):
        return self.stage == RoundStages.COMPOSING.value

    def is_guessing(self):
        return self.stage == RoundStages.GUESSING.value

    def is_done(self):
        return self.stage == RoundStages.DONE.value


class TeamWord(TimeStamped):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='team_words')
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='team_words')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='team_words')
    position = models.PositiveSmallIntegerField(_("Position"), db_index=True)

    def __str__(self):
        return str(self.word)


class TeamRound(TimeStamped):
    class Meta:
        unique_together = (('round', 'team'),)

    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='team_rounds')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='team_rounds')
    leader = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='team_rounds', null=True, blank=True)
    stage = models.PositiveSmallIntegerField(_("Stage"), default=TeamRoundStages.ACTIVE.value,
                                             choices=TeamRoundStages.choices())

    def save(self, *args, **kwargs):
        if self.leader is None:
            self.set_leader()
        super(TeamRound, self).save(*args, **kwargs)
        self.set_team_round_words()
        self.set_as_current_round()

    def get_current_stage_name(self):
        return TeamRoundStages.choice(self.stage)

    def advance_stage(self):
        if self.stage in (TeamRoundStages.ACTIVE.value, TeamRoundStages.INACTIVE.value):
            self.stage = TeamRoundStages.WAITING.value
            self.save()
        self.round.update_all_team_stages()

    def reset_stage(self):
        self.stage = TeamRoundStages.ACTIVE.value
        self.save()

    def is_waiting(self):
        return self.stage == TeamRoundStages.WAITING.value

    def is_active(self):
        return self.stage == TeamRoundStages.ACTIVE.value

    def is_done(self):
        return self.stage == TeamRoundStages.DONE.value

    def set_as_current_round(self):
        self.team.current_team_round = self
        self.team.save()

    def is_leader(self, player):
        return self.leader == player

    def set_leader(self):
        player_count = self.team.players.count()
        if player_count == 0:
            return
        offset = self.round.number % player_count
        self.leader = self.team.players.all()[offset]

    def set_team_round_words(self):
        if self.team_round_words.count() == 0:
            card = self.team.draw_card()
            for order, position in enumerate(card.value):
                team_word = self.team.team_words.get(position=position)
                self.team_round_words.create(team_word=team_word, order=order)


class TargetWord(TimeStamped):
    """Target word per round"""
    class Meta:
        unique_together = (('team_round', 'team_word'), ('team_round', 'order'),)

    team_round = models.ForeignKey(TeamRound, on_delete=models.CASCADE, related_name='team_round_words')
    team_word = models.ForeignKey(TeamWord, on_delete=models.CASCADE, related_name='team_round_words')
    order = models.PositiveSmallIntegerField(_("Order"), db_index=True)


class LeaderHint(TimeStamped):
    class Meta:
        unique_together = (('player', 'team_round_word'),)

    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    team_round_word = models.ForeignKey(TargetWord, on_delete=models.CASCADE)
    hint = models.CharField(_("Hint"), max_length=64, db_index=True, default="")


class PlayerGuess(TimeStamped):
    """Relates the target word with the player's guess"""
    class Meta:
        unique_together = (('player', 'team_round_word'),)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    team_round_word = models.ForeignKey(TargetWord, on_delete=models.CASCADE)
    guess = models.ForeignKey(TeamWord, on_delete=models.CASCADE, null=True)


class TeamGuess(TimeStamped):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    team_round_word = models.ForeignKey(TargetWord, on_delete=models.CASCADE)
    guess = models.ForeignKey(TeamWord, on_delete=models.CASCADE)


class TeamGamePoints(TimeStamped):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    wins = models.PositiveSmallIntegerField(_("Wins"))
    loses = models.PositiveSmallIntegerField(_("Loses"))

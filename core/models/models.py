import random
import string

from django.db import models
from django.utils.translation import ugettext_lazy as _

from clusterbuster.mixins.models import TimeStamped
from core.basics import PatternDeckBuilder, CardStack, Card
from core.basics.utils import CodeGenerator
from core.constants import TEAM_WORD_LIMIT

from .managers import ActiveRoomManager, ActiveGameRoomManager, RandomWordManager
from .mixins import SessionOptional, GameRoomStages, RoundStages, TeamRoundStages


# Create your models here.
class Player(TimeStamped, SessionOptional):
    class Meta:
        verbose_name = _("Player")
        verbose_name_plural = _("Players")
        ordering = ["name", "-created"]

    name = models.CharField(_("Name"), max_length=64)

    def __str__(self):
        return str(self.name)


class Team(TimeStamped, SessionOptional):
    class Meta:
        verbose_name = _("Team")
        verbose_name_plural = _("Teams")
        ordering = ["name", "-created"]

    name = models.CharField(_('Team Name'), max_length=64, default="")
    players = models.ManyToManyField(Player, blank=True)


class Room(TimeStamped, SessionOptional):
    class Meta:
        verbose_name = _("Room")
        verbose_name_plural = _("Rooms")
        ordering = ["-created"]

    code = models.SlugField(_("Code"), max_length=16)
    players = models.ManyToManyField(Player, blank=True)
    teams = models.ManyToManyField(Team, blank=True)

    objects = models.Manager()
    active_rooms = ActiveRoomManager()

    def __str__(self):
        return self.code

    def __setup_code(self):
        if not self.code:
            self.code = CodeGenerator.room_code()

    def save(self, *args, **kwargs):
        self.__setup_code()
        super(Room, self).save(*args, **kwargs)


class Word(TimeStamped):
    class Meta:
        verbose_name = _("Word")
        verbose_name_plural = _("Words")
        ordering = ["text", "-created"]

    text = models.CharField(_("Text"), max_length=32, db_index=True)
    objects = RandomWordManager()

    def __str__(self):
        return str(self.text)


class Game(TimeStamped):
    class Meta:
        verbose_name = _("Game")
        verbose_name_plural = _("Games")
        ordering = ["-created"]

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='games')
    teams = models.ManyToManyField(Team, blank=True)
    current_round = models.ForeignKey('Round', on_delete=models.SET_NULL, related_name="+", null=True, blank=True)


class GameTeam(TimeStamped):
    class Meta:
        verbose_name = _("Team")
        verbose_name_plural = _("Teams")
        ordering = ["-created"]

    name = models.CharField(_('Team Name'), max_length=64, default="")
    players = models.ManyToManyField(Player, blank=True)
    current_team_round = models.ForeignKey('TeamRound', on_delete=models.SET_NULL, related_name="+", null=True,
                                           blank=True)

    def __str__(self):
        if len(self.name) > 0:
            return str(self.name)
        else:
            return '(Game:'+str(self.game)+' ; Players:'+str(self.players)+')'

    def save(self, *args, **kwargs):
        super(GameTeam, self).save(*args, **kwargs)
        self.set_words()

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
            target_words = team_round.target_words.order_by('order').all()
            card_values = [target_word.team_word.position for target_word in target_words]
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
        return str(self.number)

    def __advance_stage(self):
        if not self.is_done():
            self.stage += 1
            self.save()

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

    def is_composing(self):
        return self.stage == RoundStages.COMPOSING.value

    def is_guessing(self):
        return self.stage == RoundStages.GUESSING.value

    def is_done(self):
        return self.stage == RoundStages.DONE.value


class TeamWord(TimeStamped):
    team = models.ForeignKey(GameTeam, on_delete=models.CASCADE, related_name='team_words')
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='team_words')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='team_words')
    position = models.PositiveSmallIntegerField(_("Position"), db_index=True)

    def __str__(self):
        return str(self.position)

    def get_text(self):
        return self.word.text


class TeamRound(TimeStamped):
    class Meta:
        unique_together = (('round', 'team'),)

    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='team_rounds')
    team = models.ForeignKey(GameTeam, on_delete=models.CASCADE, related_name='team_rounds')
    leader = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='team_rounds', null=True, blank=True)
    stage = models.PositiveSmallIntegerField(_("Stage"), default=TeamRoundStages.ACTIVE.value,
                                             choices=TeamRoundStages.choices())

    def __str__(self):
        return '(Team:'+str(self.team) + ' ; Round:'+str(self.round)+')'

    def save(self, *args, **kwargs):
        if self.leader is None:
            self.set_leader()
        super(TeamRound, self).save(*args, **kwargs)
        self.set_target_words()
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

    def get_guessing_players(self):
        return self.team.players.exclude(id=self.leader.id)

    def set_leader(self):
        player_count = self.team.players.count()
        if player_count == 0:
            return
        offset = self.round.number % player_count
        self.leader = self.team.players.all()[offset]

    def set_target_words(self):
        if self.target_words.count() == 0:
            card = self.team.draw_card()
            for order, position in enumerate(card.value):
                team_word = self.team.team_words.get(position=position)
                self.target_words.create(team_word=team_word, order=order)

    def get_non_target_words(self):
        return self.team.team_words.exclude(
            target_words__in=self.target_words.all()
        ).all()


class TargetWord(TimeStamped):
    """Target word per round"""
    class Meta:
        unique_together = (('team_round', 'team_word'), ('team_round', 'order'),)

    team_round = models.ForeignKey(TeamRound, on_delete=models.CASCADE, related_name='target_words')
    team_word = models.ForeignKey(TeamWord, on_delete=models.CASCADE, related_name='target_words')
    order = models.PositiveSmallIntegerField(_("Order"), db_index=True)

    def __str__(self):
        return '(TeamRound:'+str(self.team_round) + ' ; TeamWord:'+str(self.team_word)+' ; Order:'+str(self.order)+')'

    def save(self, *args, **kwargs):
        super(TargetWord, self).save(*args, **kwargs)
        self.get_leader_hint()

    def get_leader_hint(self):
        try:
            return self.leader_hint
        except LeaderHint.DoesNotExist:
            self.leader_hint = LeaderHint(target_word=self, leader=self.team_round.leader)
            self.leader_hint.save()
            return self.leader_hint

    def get_hint_text(self):
        return self.get_leader_hint().hint

    def get_valid_guesses(self):
        return self.player_guesses.exclude(guess=None)


class LeaderHint(TimeStamped):
    class Meta:
        unique_together = (('leader', 'target_word'),)

    leader = models.ForeignKey(Player, on_delete=models.CASCADE)
    target_word = models.OneToOneField(TargetWord, on_delete=models.CASCADE, related_name='leader_hint')
    hint = models.CharField(_("Hint"), max_length=64, db_index=True, default="")

    def __str__(self):
        return '(TargetWord:'+str(self.target_word) + ' ; Hint:'+str(self.hint)+')'


class PlayerGuess(TimeStamped):
    """Relates the target word with the player's guess"""
    class Meta:
        unique_together = (('player', 'target_word'),)
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='player_guesses')
    target_word = models.ForeignKey(TargetWord, on_delete=models.CASCADE, related_name='player_guesses')
    guess = models.ForeignKey(TeamWord, on_delete=models.CASCADE, null=True)


class TeamGuess(TimeStamped):
    team = models.ForeignKey(GameTeam, on_delete=models.CASCADE)
    target_word = models.ForeignKey(TargetWord, on_delete=models.CASCADE)
    guess = models.ForeignKey(TeamWord, on_delete=models.CASCADE)


class TeamGamePoints(TimeStamped):
    team = models.ForeignKey(GameTeam, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    wins = models.PositiveSmallIntegerField(_("Wins"))
    loses = models.PositiveSmallIntegerField(_("Loses"))

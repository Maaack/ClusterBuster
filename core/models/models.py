from django.db import models
from django.db.models import Count
from clusterbuster.mixins.models import TimeStamped
from django.utils.translation import ugettext_lazy as _
from core.models.mixins import SessionOptional, SessionRequired

GAME_TEAM_LIMIT = 2
GAME_ROUND_LIMIT = 8
TEAM_PLAYER_LIMIT = 4
TEAM_WORD_LIMIT = 4
POSITION_COUNT = 3


# Create your models here.
class Player(TimeStamped, SessionRequired):
    class Meta:
        verbose_name = _("Player")
        verbose_name_plural = _("Players")
        ordering = ["name", "-created"]

    name = models.CharField(_("Name"), max_length=24)

    def __str__(self):
        return str(self.name)


class Word(TimeStamped):
    class Meta:
        verbose_name = _("Word")
        verbose_name_plural = _("Words")
        ordering = ["text", "-created"]

    text = models.CharField(_("Text"), max_length=16, db_index=True)

    def __str__(self):
        return str(self.text)


class Team(TimeStamped):
    class Meta:
        verbose_name = _("Team")
        verbose_name_plural = _("Teams")
        ordering = ["-created"]

    players = models.ManyToManyField(Player, blank=True)

    def join(self, player):
        if type(player) is Player and not self.has_max_players():
            self.players.add(player)
            return True
        return False

    def has_player(self, player):
        return self.players.filter(pk=player.pk).exists()

    def has_max_players(self):
        return self.players.count() >= TEAM_PLAYER_LIMIT


class Game(TimeStamped, SessionRequired):
    class Meta:
        verbose_name = _("Game")
        verbose_name_plural = _("Games")
        ordering = ["-created"]

    teams = models.ManyToManyField(Team, blank=True)
    players = models.ManyToManyField(Player, blank=True)

    def save(self, *args, **kwargs):
        super(Game, self).save(*args, **kwargs)
        self.create_teams()

    def create_teams(self, team_count=GAME_TEAM_LIMIT):
        current_team_count = self.teams.count()
        team_slots = GAME_TEAM_LIMIT - current_team_count
        if team_slots > 0:
            new_teams = min(team_slots, team_count)
            for team_number in range(new_teams):
                self.teams.create()

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
            self.rounds.create(number=self.get_current_round_number()+1)

    def get_current_round(self):
        return self.rounds.order_by('-number').first()

    def get_current_round_number(self):
        current_round = self.get_current_round()
        if current_round:
            return current_round.number
        else:
            return 0

    def is_last_round(self):
        return self.get_current_round_number() >= GAME_ROUND_LIMIT


class Round(TimeStamped):
    class Meta:
        verbose_name = _("Round")
        verbose_name_plural = _("Rounds")
        ordering = ["-created"]

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='rounds')
    number = models.PositiveSmallIntegerField(_("Round Number"), db_index=True)


class TeamWord(TimeStamped):
    class Meta:
        default_related_name = 'team_words'

    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    position = models.PositiveSmallIntegerField(_("Position"), db_index=True)


class RoundLeader(TimeStamped):
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)


class TeamRoundWordPosition(TimeStamped):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    word = models.ForeignKey(TeamWord, on_delete=models.CASCADE)
    position = models.PositiveSmallIntegerField(_("Position"), db_index=True)


class Hint(TimeStamped):
    class Meta:
        verbose_name = _("Hint")
        verbose_name_plural = _("Hints")
        ordering = ["-created"]

    text = models.CharField(_("Text"), max_length=64, db_index=True)


class RoundHint(TimeStamped):
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    hint = models.ForeignKey(Hint, on_delete=models.CASCADE)
    position = models.PositiveSmallIntegerField(_("Position"), db_index=True)


class PlayerGuess(TimeStamped):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    hint = models.ForeignKey(RoundHint, on_delete=models.CASCADE)
    guess = models.ForeignKey(TeamWord, on_delete=models.CASCADE)


class TeamGuess(TimeStamped):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    hint = models.ForeignKey(RoundHint, on_delete=models.CASCADE)
    guess = models.ForeignKey(TeamWord, on_delete=models.CASCADE)


class TeamGamePoints(TimeStamped):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    wins = models.PositiveSmallIntegerField(_("Wins"))
    loses = models.PositiveSmallIntegerField(_("Loses"))
import random, string
from django.db import models
from django.db.models import Count
from clusterbuster.mixins.models import TimeStamped
from django.utils.translation import ugettext_lazy as _
from .mixins import SessionOptional, SessionRequired, GameRoomStages
from .managers import ActiveGameRoomManager, RandomWordManager
from .mixins import SessionOptional, GameRoomStages

GAME_TEAM_LIMIT = 2
GAME_ROUND_LIMIT = 8
TEAM_PLAYER_LIMIT = 4
TEAM_WORD_LIMIT = 4
POSITION_COUNT = 3
GAME_ROOM_CODE_LENGTH = 4


# Create your models here.
class Player(TimeStamped, SessionOptional):
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
    objects = RandomWordManager()

    def __str__(self):
        return str(self.text)


class Game(TimeStamped, SessionOptional):
    class Meta:
        verbose_name = _("Game")
        verbose_name_plural = _("Games")
        ordering = ["-created"]

    players = models.ManyToManyField(Player, blank=True)

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
        has_room = False
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


class GameRoom(TimeStamped):
    class Meta:
        verbose_name = _("Game Room")
        verbose_name_plural = _("Game Rooms")
        ordering = ["-created"]

    code = models.SlugField(_("Code"), max_length=16)
    stage = models.PositiveSmallIntegerField(_("Stage"), default=GameRoomStages.OPEN.value,
                                             choices=GameRoomStages.choices())
    game = models.OneToOneField(Game, on_delete=models.CASCADE)

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
        return self.game.get_current_round()

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
                self.team_words.create(word=Word.objects.random(), game=self.game, position=i+1)


class Round(TimeStamped):
    class Meta:
        verbose_name = _("Round")
        verbose_name_plural = _("Rounds")
        ordering = ["-created"]

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='rounds')
    number = models.PositiveSmallIntegerField(_("Round Number"), db_index=True)

    def __str__(self):
        return "Round " + str(self.number)

    def save(self, *args, **kwargs):
        super(Round, self).save(*args, **kwargs)
        self.set_team_leaders()

    def set_team_leaders(self):
        if self.team_leaders.count() == 0:
            for team in self.game.teams.all():
                player_count = team.players.count()
                if player_count == 0:
                    continue
                leader = team.players.all()[self.number % player_count]
                self.team_leaders.create(team=team, player=leader)

    def is_leader(self, player):
        return self.team_leaders.filter(player=player).exists()


class TeamWord(TimeStamped):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='team_words')
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='team_words')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='team_words')
    position = models.PositiveSmallIntegerField(_("Position"), db_index=True)

    def __str__(self):
        return str(self.word)


class RoundTeamLeader(TimeStamped):
    class Meta:
        unique_together = (('round', 'team'),)

    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='team_leaders')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='team_leaders')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='team_leaders')

    def __str__(self):
        return str(self.player)


class RoundTeamWord(TimeStamped):
    class Meta:
        unique_together = (('round', 'team_word'), ('round', 'team', 'order'),)

    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='round_team_words')
    team_word = models.ForeignKey(TeamWord, on_delete=models.CASCADE, related_name='round_team_words')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='round_team_words')
    order = models.PositiveSmallIntegerField(_("Order"), db_index=True)


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
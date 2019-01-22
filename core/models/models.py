from django.db import models
from django.utils.translation import ugettext_lazy as _

from clusterbuster.mixins.models import TimeStamped
from core.basics.utils import CodeGenerator

from . import mixins, managers, choices


# Create your models here.
class Player(TimeStamped, mixins.SessionOptional):
    """
    Players represent individual sessions logging in to play.
    """
    class Meta:
        verbose_name = _("Player")
        verbose_name_plural = _("Players")
        ordering = ["name", "-created"]

    name = models.CharField(_("Name"), max_length=64)

    def __str__(self):
        return str(self.name)


class Team(TimeStamped, mixins.SessionOptional):
    """
    Teams are a collections of players with a common name.
    """
    class Meta:
        verbose_name = _("Team")
        verbose_name_plural = _("Teams")
        ordering = ["name", "-created"]

    name = models.CharField(_('Team Name'), max_length=64, default="")
    players = models.ManyToManyField(Player, blank=True)

    def __str__(self):
        return str(self.name)


class Room(TimeStamped, mixins.SessionOptional, mixins.GamesRoom):
    """
    Rooms are for players and teams to join together.
    """
    class Meta:
        verbose_name = _("Room")
        verbose_name_plural = _("Rooms")
        ordering = ["-created"]

    code = models.SlugField(_("Code"), max_length=16)
    players = models.ManyToManyField(Player, blank=True)
    teams = models.ManyToManyField(Team, blank=True)

    objects = models.Manager()
    active_rooms = managers.ActiveRoomManager()

    def __str__(self):
        return self.code

    def __setup_code(self):
        if not self.code:
            self.code = CodeGenerator.room_code()

    def save(self, *args, **kwargs):
        self.__setup_code()
        super(Room, self).save(*args, **kwargs)


class Word(TimeStamped):
    """
    Words that can be used for word based games.
    """
    class Meta:
        verbose_name = _("Word")
        verbose_name_plural = _("Words")
        ordering = ["text", "-created"]

    text = models.CharField(_("Text"), max_length=32, db_index=True)
    objects = managers.RandomWordManager()

    def __str__(self):
        return str(self.text)


class Game(TimeStamped, mixins.RoundsGame):
    class Meta:
        verbose_name = _("Game")
        verbose_name_plural = _("Games")
        ordering = ["-created"]

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='games')
    teams = models.ManyToManyField(Team, blank=True, through='Party', related_name='games')

    def __str__(self):
        return str(self.room)


class Party(TimeStamped, mixins.RoundsParty):
    """
    An intermediate between games and teams.
    """
    class Meta:
        verbose_name = _("Party")
        verbose_name_plural = _("Parties")
        ordering = ["-created"]
        unique_together = (('game', 'team'),)

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='parties')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='parties')

    def __str__(self):
        return '(Game: '+str(self.game)+' ; Team: '+str(self.team)+' )'


class PartyWord(TimeStamped):
    """
    The secret word for team they get at the start of the game.
    """
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='party_words')
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='party_words')
    position = models.PositiveSmallIntegerField(_("Position"), db_index=True)

    def __str__(self):
        return str(self.position)

    def get_text(self):
        return self.word.text


class Round(TimeStamped, mixins.StagesRound):
    """
    Rounds break up repeatable parts of a game.
    """
    class Meta:
        verbose_name = _("Round")
        verbose_name_plural = _("Rounds")
        ordering = ["-created"]

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='rounds')
    parties = models.ManyToManyField(Party, blank=True, through='PartyRound', related_name='rounds')
    number = models.PositiveSmallIntegerField(_("Round Number"), db_index=True)

    def __str__(self):
        return str(self.number)


class PartyRound(TimeStamped, mixins.StagesPartyRound, mixins.RoundLeader):
    """
    An intermediate between parties and rounds.
    """

    class Meta:
        unique_together = (('party', 'round'),)

    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='party_rounds')
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='party_rounds')

    def __str__(self):
        return '(Party:' + str(self.party) + ' ; Round:' + str(self.round) + ')'


class TargetWord(TimeStamped):
    """
    Target word for teams per round.
    """
    class Meta:
        unique_together = (('party_round', 'party_word'), ('party_round', 'order'),)

    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='target_words')
    party_round = models.ForeignKey(PartyRound, on_delete=models.CASCADE, related_name='target_words')
    party_word = models.ForeignKey(PartyWord, on_delete=models.CASCADE, related_name='target_words')
    order = models.PositiveSmallIntegerField(_("Order"), db_index=True)

    def __str__(self):
        return '(PartyRound:' + str(self.party_round) + ' ; PartyWord:' + str(self.party_word) + ' ; Order:' + str(self.order) + ')'

    def save(self, *args, **kwargs):
        super(TargetWord, self).save(*args, **kwargs)
        self.get_leader_hint()

    def get_leader_hint(self):
        try:
            return self.leader_hint
        except LeaderHint.DoesNotExist:
            self.leader_hint = LeaderHint(target_word=self, leader=self.party_round.leader)
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
    """
    Relates the target word with the player's guess
    """

    class Meta:
        verbose_name = _("Player Guess")
        verbose_name_plural = _("Player Guesses")
        ordering = ["-created"]
        unique_together = (('player', 'target_word'),)

    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='player_guesses')
    target_word = models.ForeignKey(TargetWord, on_delete=models.CASCADE, related_name='player_guesses')
    guess = models.ForeignKey(PartyWord, on_delete=models.CASCADE, null=True)


class PartyGuess(TimeStamped):
    party = models.ForeignKey(Party, on_delete=models.CASCADE)
    target_word = models.ForeignKey(TargetWord, on_delete=models.CASCADE)
    guess = models.ForeignKey(PartyWord, on_delete=models.CASCADE)


class TeamGamePoints(TimeStamped):
    team = models.ForeignKey(Party, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    wins = models.PositiveSmallIntegerField(_("Wins"))
    loses = models.PositiveSmallIntegerField(_("Loses"))

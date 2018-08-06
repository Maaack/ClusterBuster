from django.db import models
from clusterbuster.mixins.models import TimeStamped, TimeStampedOwnable, Owned
from django.utils.translation import ugettext_lazy as _


# Create your models here.
class Player(TimeStamped, Owned):
    class Meta:
        verbose_name = _("Player")
        verbose_name_plural = _("Players")
        ordering = ["-created"]

    name = models.CharField(_("Name"), max_length=24)


class Word(TimeStamped):
    class Meta:
        verbose_name = _("Word")
        verbose_name_plural = _("Words")
        ordering = ["-created"]

    text = models.CharField(_("Text"), max_length=16)


class Team(TimeStampedOwnable):
    class Meta:
        verbose_name = _("Team")
        verbose_name_plural = _("Teams")
        ordering = ["-created"]

    players = models.ManyToManyField(Player)


class Game(TimeStampedOwnable):
    class Meta:
        verbose_name = _("Game")
        verbose_name_plural = _("Games")
        ordering = ["-created"]

    teams = models.ManyToManyField(Team)


class TeamGameWord(TimeStamped):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField(_("Order"))


class Round(TimeStamped):
    class Meta:
        verbose_name = _("Round")
        verbose_name_plural = _("Rounds")
        ordering = ["-created"]

    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    number = models.PositiveSmallIntegerField(_("Round Number"))


class RoundLeader(TimeStamped):
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)


class TeamRoundWordOrder(TimeStamped):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    word = models.ForeignKey(TeamGameWord, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField(_("Order"))


class Hint(TimeStamped):
    class Meta:
        verbose_name = _("Hint")
        verbose_name_plural = _("Hints")
        ordering = ["-created"]

    text = models.CharField(_("Text"), max_length=64)


class RoundHint(TimeStamped):
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    hint = models.ForeignKey(Hint, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField(_("Order"))


class PlayerGuess(TimeStamped):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    hint = models.ForeignKey(RoundHint, on_delete=models.CASCADE)
    guess = models.ForeignKey(TeamGameWord, on_delete=models.CASCADE)


class TeamGuess(TimeStamped):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    hint = models.ForeignKey(RoundHint, on_delete=models.CASCADE)
    guess = models.ForeignKey(TeamGameWord, on_delete=models.CASCADE)


class TeamGamePoints(TimeStamped):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    wins = models.PositiveSmallIntegerField(_("Wins"))
    loses = models.PositiveSmallIntegerField(_("Loses"))
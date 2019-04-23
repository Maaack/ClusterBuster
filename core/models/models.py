from django.db import models
from django.utils.translation import ugettext_lazy as _

from clusterbuster.mixins.models import TimeStamped

from . import managers


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


class State(TimeStamped):
    """
    States define sections of the Game, like stages, rounds, and turns.
    """
    slug = models.SlugField(_("Slug"), max_length=32)
    name = models.CharField(_("Name"), max_length=64, blank=True)

    class Meta:
        verbose_name = _("State")
        verbose_name_plural = _("States")

    def __str__(self):
        return str(self.slug)


class StateMachine(models.Model):
    slug = models.SlugField(_("Slug"), max_length=32)
    root_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="+")

    class Meta:
        verbose_name = _("State Machine")
        verbose_name_plural = _("State Machines")

    def __str__(self):
        return str(self.slug)


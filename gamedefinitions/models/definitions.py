from django.db import models
from django.utils.translation import ugettext_lazy as _

from clusterbuster.mixins import TimeStamped


class Rule(TimeStamped):
    """
    Rules define how the game is played.
    """
    slug = models.SlugField(_("Slug"), max_length=64)
    description = models.TextField(_("Description"), default='')

    class Meta:
        verbose_name = _("Rule")
        verbose_name_plural = _("Rules")
        ordering = ["-created"]

    def __str__(self):
        return str(self.slug)


class GameDefinition(TimeStamped):
    slug = models.SlugField(_("Slug"), max_length=64)
    title = models.CharField(_("Title"), max_length=128, default='')
    description = models.TextField(_("Description"), default='')
    rules = models.ManyToManyField(Rule, blank=True, related_name="game_definitions")
    first_rule = models.ForeignKey(Rule, on_delete=models.CASCADE, related_name='+')

    class Meta:
        verbose_name = _("Game Definition")
        verbose_name_plural = _("Games Definitions")
        ordering = ["-created"]

    def __str__(self):
        return str(self.slug)

    def __init__(self, *args, **kwargs):
        super(GameDefinition, self).__init__(*args, **kwargs)

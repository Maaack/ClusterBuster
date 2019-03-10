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


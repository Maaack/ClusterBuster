from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.sessions.models import Session


class SessionRequired(models.Model):
    class Meta:
        abstract = True

    session = models.ForeignKey(Session, on_delete=models.CASCADE, verbose_name=_("Session"),
                                related_name="%(app_label)s_%(class)s_related")


class SessionOptional(models.Model):
    class Meta:
        abstract = True

    session = models.ForeignKey(Session, on_delete=models.SET_NULL, verbose_name=_("Session"), null=True, blank=True,
                                related_name="%(app_label)s_%(class)s_related")

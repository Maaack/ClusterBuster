from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _


class TimeStamped(models.Model):
    class Meta:
        abstract = True

    created = models.DateTimeField(null=True, editable=False)
    updated = models.DateTimeField(null=True, editable=False)

    def save(self, *args, **kwargs):
        _now = now()
        self.updated = _now
        if not self.id:
            self.created = _now
        super(TimeStamped, self).save(*args, **kwargs)


class RawTitle(models.Model):
    class Meta:
        abstract = True

    raw_title = models.CharField(_("Raw Title"), max_length=100)
    title = models.CharField(_("Title"), max_length=100, blank=True, null=True, default='')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.title = self.raw_title.strip().capitalize()
        return super(RawTitle, self).save(*args, **kwargs)


class RawText(models.Model):
    class Meta:
        abstract = True

    raw_text = models.TextField(_("Raw Text"), blank=True, null=True, default='')
    text = models.TextField(_("Text"), blank=True, null=True, default='')
    snippet = models.CharField(_("Snippet"), max_length=25, blank=True, null=True, default='')

    def __str__(self):
        return self.snippet

    def save(self, *args, **kwargs):
        self.text = self.raw_text.strip()
        self.snippet = self.text[:25]
        return super(RawText, self).save(*args, **kwargs)

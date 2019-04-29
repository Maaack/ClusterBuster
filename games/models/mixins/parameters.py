from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

__all__ = ['BaseValue', 'BaseNumericValue', 'BaseIntegerValue', 'BaseFloatValue', 'BaseCharacterValue',
           'BaseBooleanValue', 'BaseParameter']


class BaseValue(models.Model):
    value = models.BooleanField(_("Value"), blank=True, null=True, default=None)

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.value)


class BaseNumericValue(BaseValue):
    value = models.IntegerField(_("Value"), blank=True, null=True, default=None)

    class Meta:
        abstract = True

    def __eq__(self, other):
        if not isinstance(other, BaseNumericValue):
            return False
        return self.value == other.value

    def __ne__(self, other):
        if not isinstance(other, BaseNumericValue):
            return True
        return self.value != other.value

    def __gt__(self, other):
        if not isinstance(other, BaseNumericValue):
            return False
        return self.value > other.value

    def __lt__(self, other):
        if not isinstance(other, BaseNumericValue):
            return False
        return self.value < other.value

    def __ge__(self, other):
        if not isinstance(other, BaseNumericValue):
            return False
        return self.value >= other.value

    def __le__(self, other):
        if not isinstance(other, BaseNumericValue):
            return False
        return self.value <= other.value


class BaseIntegerValue(BaseNumericValue):
    value = models.IntegerField(_("Value"), blank=True, null=True, default=None)

    class Meta:
        abstract = True


class BaseFloatValue(BaseNumericValue):
    value = models.FloatField(_("Value"), blank=True, null=True, default=None)

    class Meta:
        abstract = True


class BaseCharacterValue(BaseValue):
    value = models.CharField(_("Value"), max_length=255, blank=True, null=True, default=None)

    class Meta:
        abstract = True


class BaseBooleanValue(BaseValue):
    value = models.NullBooleanField(_("Value"), default=None)

    class Meta:
        abstract = True


class BaseParameter(models.Model):
    """
    Parameters store key / value pairs in Parameter Dictionaries.
    """
    key = models.SlugField(_("Key"), max_length=255, db_index=True)
    value = GenericForeignKey('content_type', 'object_id')
    object_id = models.PositiveIntegerField(_('Object ID'), blank=True, null=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, blank=True, null=True, related_name='+')

    class Meta:
        abstract = True

    def __str__(self):
        try:
            return str(self.key) + ": " + str(self.value)
        except AttributeError:
            return str(self.key) + ": (Deleted)"

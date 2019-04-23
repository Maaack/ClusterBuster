from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from clusterbuster.mixins import TimeStamped

from .mixins import BaseValue, BaseNumericValue

__all__ = ['IntegerValue', 'FloatValue', 'CharacterValue', 'BooleanValue', 'ParameterDictionary', 'Parameter']


class IntegerValue(BaseNumericValue):
    value = models.IntegerField(_("Value"), blank=True, null=True, default=None)


class FloatValue(BaseNumericValue):
    value = models.FloatField(_("Value"), blank=True, null=True, default=None)


class CharacterValue(BaseValue):
    value = models.CharField(_("Value"), max_length=255, blank=True, null=True, default=None)


class BooleanValue(BaseValue):
    value = models.NullBooleanField(_("Value"), default=None)


class ParameterDictionary(TimeStamped):
    """
    Parameters store all data about a specific game and the state.
    """
    class Meta:
        verbose_name = _("Parameter Dictionary")
        verbose_name_plural = _("Parameter Dictionaries")
        ordering = ["-created"]

    @staticmethod
    def __get_model_value(raw_value):
        if isinstance(raw_value, models.Model):
            return raw_value
        elif isinstance(raw_value, int):
            return IntegerValue.objects.create(value=raw_value)
        elif isinstance(raw_value, float):
            return FloatValue.objects.create(value=raw_value)
        elif isinstance(raw_value, str):
            return CharacterValue.objects.create(value=raw_value)
        elif isinstance(raw_value, bool):
            return BooleanValue.objects.create(value=raw_value)
        else:
            raise ValueError('raw_value must be a recognized type.')

    @staticmethod
    def __get_key_from_args(*args):
        return "_".join(str(i).lower() for i in args)

    def get_parameter(self, key_args):
        if isinstance(key_args, str):
            key_args = (key_args,)
        key_string = ParameterDictionary.__get_key_from_args(*key_args)
        parameter, create = Parameter.objects.get_or_create(dictionary=self, key=key_string)
        return parameter

    def get_parameter_value(self, key_args):
        parameter = self.get_parameter(key_args)
        if isinstance(parameter.value, BaseValue):
            return parameter.value.value
        return parameter.value

    def set_parameter_value(self, key_args, value):
        parameter = self.get_parameter(key_args)
        parameter.value = ParameterDictionary.__get_model_value(value)
        parameter.save()


class Parameter(TimeStamped):
    """
    Parameters store key / value pairs in Parameter Dictionaries.
    """
    dictionary = models.ForeignKey(ParameterDictionary, on_delete=models.CASCADE, related_name='parameters')
    key = models.SlugField(_("Key"), max_length=255, db_index=True)
    value = GenericForeignKey('content_type', 'object_id')
    object_id = models.PositiveIntegerField(_('Object ID'), blank=True, null=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        verbose_name = _("Parameter")
        verbose_name_plural = _("Parameters")
        ordering = ["-created"]
        unique_together = ('dictionary', 'key')

    def __str__(self):
        return str(self.key) + ": " + str(self.value)

    def __eq__(self, other):
        if not isinstance(other, Parameter):
            return False
        return self.value == other.value

    def __ne__(self, other):
        if not isinstance(other, Parameter):
            return False
        return self.value != other.value

    def __gt__(self, other):
        if not isinstance(other, Parameter):
            return False
        return self.value > other.value

    def __lt__(self, other):
        if not isinstance(other, Parameter):
            return False
        return self.value < other.value

    def __ge__(self, other):
        if not isinstance(other, Parameter):
            return False
        return self.value >= other.value

    def __le__(self, other):
        if not isinstance(other, Parameter):
            return False
        return self.value <= other.value


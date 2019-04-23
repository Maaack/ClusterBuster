from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from clusterbuster.mixins import TimeStamped

from .mixins import BaseValue, BaseNumericValue

__all__ = ['IntegerValue', 'FloatValue', 'CharacterValue', 'BooleanValue', 'ParameterDictionary',
           'Parameter', 'ParameterUpdate']


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
            return IntegerValue(value=raw_value)
        elif isinstance(raw_value, float):
            return FloatValue(value=raw_value)
        elif isinstance(raw_value, str):
            return CharacterValue(value=raw_value)
        elif isinstance(raw_value, bool):
            return BooleanValue(value=raw_value)
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
        old_value = parameter.value
        new_value = ParameterDictionary.__get_model_value(value)
        if old_value != new_value:
            new_value.save()
            ParameterUpdate.objects.create(parameter=parameter, old_value=old_value, new_value=new_value)
            parameter.value = new_value
            parameter.save()


class Parameter(TimeStamped):
    """
    Parameters store key / value pairs in Parameter Dictionaries.
    """
    dictionary = models.ForeignKey(ParameterDictionary, on_delete=models.CASCADE, related_name='parameters')
    key = models.SlugField(_("Key"), max_length=255, db_index=True)
    value = GenericForeignKey('content_type', 'object_id')
    object_id = models.PositiveIntegerField(_('Object ID'), blank=True, null=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, blank=True, null=True, related_name='+')

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
            return True
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


class ParameterUpdate(TimeStamped):
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE, related_name='updates')
    old_value = GenericForeignKey('old_content_type', 'old_object_id')
    old_object_id = models.PositiveIntegerField(_('Object ID'), blank=True, null=True)
    old_content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, blank=True, null=True,
                                         related_name='+')
    new_value = GenericForeignKey('new_content_type', 'new_object_id')
    new_object_id = models.PositiveIntegerField(_('Object ID'), blank=True, null=True)
    new_content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, blank=True, null=True,
                                         related_name='+')

    class Meta:
        verbose_name = _("Parameter Update")
        verbose_name_plural = _("Parameter Updates")
        ordering = ["-created"]

    def __str__(self):
        return str(self.parameter.key) + ": " + str(self.old_value) + " -> " + str(self.new_value)

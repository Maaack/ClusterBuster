from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from clusterbuster.mixins import TimeStamped

from .mixins.parameters import *

__all__ = ['IntegerValue', 'FloatValue', 'CharacterValue', 'BooleanValue', 'ParameterDictionary',
           'Parameter', 'ParameterUpdate']


class IntegerValue(BaseIntegerValue):
    pass


class FloatValue(BaseFloatValue):
    pass


class CharacterValue(BaseCharacterValue):
    pass


class BooleanValue(BaseBooleanValue):
    pass


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
    def __get_str_from_iter(args):
        try:
            return "_".join(str(i) for i in args)
        except TypeError:
            return str(args)

    def get_parameter(self, key):
        if not isinstance(key, str):
            key = ParameterDictionary.__get_str_from_iter(key)
        parameter, create = Parameter.objects.get_or_create(dictionary=self, key=key)
        return parameter

    def get_value(self, key):
        parameter = self.get_parameter(key)
        if isinstance(parameter.value, BaseValue):
            return parameter.value.value
        return parameter.value

    def set_value(self, key, value):
        parameter = self.get_parameter(key)
        old_value = parameter.value
        new_value = ParameterDictionary.__get_model_value(value)
        if old_value != new_value:
            new_value.save()
            ParameterUpdate.objects.create(parameter=parameter, old_value=old_value, new_value=new_value)
            parameter.value = new_value
            parameter.save()


class Parameter(BaseParameter, TimeStamped):
    """
    Parameters store key / value pairs in Parameter Dictionaries.
    """
    dictionary = models.ForeignKey(ParameterDictionary, on_delete=models.CASCADE, related_name='parameters')

    class Meta:
        verbose_name = _("Parameter")
        verbose_name_plural = _("Parameters")
        ordering = ["-created"]
        unique_together = ('dictionary', 'key')

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

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey


class BaseValue(models.Model):

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        self.value = None
        super().__init__(*args, **kwargs)

    def __str__(self):
        return str(self.value)


class BaseNumericValue(BaseValue):

    class Meta:
        abstract = True

    def __eq__(self, other):
        if not isinstance(other, BaseNumericValue):
            return False
        return self.value == other.value

    def __ne__(self, other):
        if not isinstance(other, BaseNumericValue):
            return False
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


class ParameterAbstract(models.Model):
    key = models.SlugField(_("Key"), max_length=255, db_index=True)
    value = GenericForeignKey('content_type', 'object_id')

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.key) + ": " + str(self.value)

    def __eq__(self, other):
        if not isinstance(other, ParameterAbstract):
            return False
        return self.value == other.value

    def __ne__(self, other):
        if not isinstance(other, ParameterAbstract):
            return False
        return self.value != other.value

    def __gt__(self, other):
        if not isinstance(other, ParameterAbstract):
            return False
        return self.value > other.value

    def __lt__(self, other):
        if not isinstance(other, ParameterAbstract):
            return False
        return self.value < other.value

    def __ge__(self, other):
        if not isinstance(other, ParameterAbstract):
            return False
        return self.value >= other.value

    def __le__(self, other):
        if not isinstance(other, ParameterAbstract):
            return False
        return self.value <= other.value

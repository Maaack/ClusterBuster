from django.conf import settings
from enum import Enum


class ChoiceEnum(Enum):
    @classmethod
    def choices(cls):
        return tuple((i.value, i.name) for i in cls)

    @classmethod
    def choice(cls, choice):
        for i in cls:
            if i.value == choice:
                return i.name
        return ""


def get_user_model_name():
    """
    Returns the app_label.object_name string for the user model.
    """
    return getattr(settings, "AUTH_USER_MODEL", "auth.User")



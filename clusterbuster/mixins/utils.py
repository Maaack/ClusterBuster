from django.conf import settings
from enum import Enum

import random
import string


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


class CodeGenerator:
    ROOM_CODE_LENGTH = 4
    DEFAULT_CODE_LENGTH = 4
    LOBBY_CODE_LENGTH = 4
    GAME_CODE_LENGTH = 6

    @staticmethod
    def get_code(length=DEFAULT_CODE_LENGTH):
        return ''.join(random.choice(string.ascii_uppercase) for _ in range(length))

    @staticmethod
    def room_code(length=ROOM_CODE_LENGTH):
        return CodeGenerator.get_code(length)

    @staticmethod
    def lobby_code(length=LOBBY_CODE_LENGTH):
        return CodeGenerator.get_code(length)

    @staticmethod
    def game_code(length=GAME_CODE_LENGTH):
        return CodeGenerator.get_code(length)


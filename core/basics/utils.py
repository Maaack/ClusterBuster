import random
import string

from core.constants import ROOM_CODE_LENGTH


class CodeGenerator:
    @staticmethod
    def room_code(length=ROOM_CODE_LENGTH):
        return ''.join(random.choice(string.ascii_uppercase) for _ in range(length))


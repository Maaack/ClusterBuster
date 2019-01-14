import random
from django.db import models
from django.db.models import Count
from core.models.choices import GameStages

GAME_ROOM_ACTIVE_STAGES = [
    GameStages.OPEN.value,
    GameStages.PLAYING.value,
    GameStages.PAUSED.value,
]


class ActiveRoomManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(session=None)


class RandomWordManager(models.Manager):
    def random(self):
        count = self.aggregate(count=Count('id'))['count']
        if count == 0:
            raise ValueError
        random_index = random.randint(0, count - 1)
        return self.all()[random_index]
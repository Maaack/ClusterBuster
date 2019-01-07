import random
from django.db import models
from django.db.models import Count
from core.models.mixins import GameRoomStages

GAME_ROOM_ACTIVE_STAGES = [GameRoomStages.OPEN.value, GameRoomStages.PLAYING.value, GameRoomStages.PAUSED.value]


class ActiveGameRoomManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(stage__in=GAME_ROOM_ACTIVE_STAGES)


class RandomWordManager(models.Manager):
    def random(self):
        count = self.aggregate(count=Count('id'))['count']
        if count == 0:
            raise ValueError
        random_index = random.randint(0, count - 1)
        return self.all()[random_index]
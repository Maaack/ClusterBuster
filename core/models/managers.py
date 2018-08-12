from django.db import models
from core.models.mixins import GameRoomStages

GAME_ROOM_ACTIVE_STAGES = [GameRoomStages.OPEN.value, GameRoomStages.PLAYING.value, GameRoomStages.PAUSED.value]


class ActiveGameRoomManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(stage__in=GAME_ROOM_ACTIVE_STAGES)
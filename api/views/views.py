from rest_framework import viewsets
from .serializers import *


class LobbyViewSet(viewsets.ModelViewSet):
    queryset = Lobby.active_lobbies.all()
    serializer_class = LobbySerializer


class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer

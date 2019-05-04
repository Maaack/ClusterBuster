from rest_framework import serializers

from lobbies.models import Lobby, Player, Team, Activity


# Serializers define the API representation.
class LobbySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Lobby
        fields = ('code', 'players', 'teams', 'current_activity')


class PlayerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Player
        fields = ('name',)


class TeamSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Team
        fields = ('name', 'players')


class ActivitySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Activity
        fields = ('lobby', 'name', 'link')

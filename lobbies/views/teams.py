from django.views import generic

from ..models import Team

from .contexts import PlayerContext, Player2TeamContext
from .mixins import CheckPlayerView


class TeamCreate(generic.CreateView):
    model = Team
    fields = ['name']


class TeamUpdate(generic.UpdateView):
    model = Team
    fields = ['name']


class TeamDetail(generic.DetailView, CheckPlayerView):
    model = Team

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        team = self.get_object()  # type: Team
        current_player = self.get_current_player()
        if current_player:
            player_data = PlayerContext.load(current_player)
            data.update(player_data)
            player_team_data = Player2TeamContext.load(current_player, team)
            data.update(player_team_data)
        return data

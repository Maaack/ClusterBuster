from django.views import generic
from django.http import HttpResponse
from django.shortcuts import redirect, reverse
from django.template import loader

from ..models import Lobby

from .contexts import PlayerContext, TeamContext, Player2LobbyContext, Player2TeamContext
from .mixins import CheckPlayerView


def index_view(request):
    template = loader.get_template('lobbies/index.html')
    return HttpResponse(template.render({}, request))


class LobbyCreate(generic.CreateView, CheckPlayerView):
    model = Lobby
    fields = []

    def dispatch(self, request, *args, **kwargs):
        player = self.get_current_player()
        if player is None:
            return redirect('player_create')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.request.session.save()
        new_lobby = form.instance  # type: Lobby
        new_lobby.session_id = self.request.session.session_key
        response = super().form_valid(form)
        player = self.get_current_player()
        new_lobby.join(player)
        return response

    def get_success_url(self):
        return reverse('lobby_detail', kwargs={'slug': self.object.code})


class LobbyList(generic.ListView):
    context_object_name = 'active_lobbies'

    def get_queryset(self):
        return Lobby.active_lobbies.all()


class LobbyDetail(generic.DetailView, CheckPlayerView):
    model = Lobby
    slug_field = 'code'

    def get_queryset(self):
        return Lobby.active_lobbies.all()

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        lobby = self.get_object()  # type: Lobby
        current_player = self.get_current_player()
        if current_player:
            player_data = PlayerContext.load(current_player)
            data.update(player_data)
            player_lobby_data = Player2LobbyContext.load(current_player, lobby)
            data.update(player_lobby_data)
        players = lobby.players.all()
        players_data = list()
        for player in players:
            player_data = PlayerContext.load(player)
            player_lobby_data = Player2LobbyContext.load(player, lobby)
            player_data.update(player_lobby_data)
            player_data['is_player'] = player == current_player
            players_data.append(player_data)
        data['players'] = players_data
        teams = lobby.teams.all()
        teams_data = list()
        for team in teams:
            team_data = TeamContext.load(team)
            if current_player:
                player_team_data = Player2TeamContext.load(current_player, team)
                team_data.update(player_team_data)
            teams_data.append(team_data)
        data['teams'] = teams_data
        data['activity_options'] = lobby.get_activity_options()

        return data


class JoinLobby(generic.RedirectView, generic.detail.SingleObjectMixin, CheckPlayerView):
    model = Lobby
    pattern_name = 'lobby_detail'
    slug_field = 'code'

    def get_redirect_url(self, *args, **kwargs):
        player = self.get_current_player()
        if not player:
            raise Exception('Player must be logged in.')
        lobby = self.get_object()
        lobby.join(player)
        return super().get_redirect_url(*args, **kwargs)

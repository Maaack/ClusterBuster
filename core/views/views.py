from django.shortcuts import get_object_or_404
from django.views import generic
from django.urls import reverse_lazy

from rooms.models import Room
from games.models import Game
from core.definitions import ClusterBuster

from rooms.views.mixins import CheckPlayerView
from rooms.views.contexts import PlayerContext, TeamContext, Player2RoomContext, Player2TeamContext

from .forms import LeaderHintsForm


class StartGame(generic.RedirectView, generic.detail.SingleObjectMixin):
    model = Room
    pattern_name = 'room_detail'
    slug_field = 'code'

    def get_redirect_url(self, *args, **kwargs):
        room = get_object_or_404(Room, code=kwargs['slug'])
        game = Game.objects.create()
        game.setup("cluster_buster", room=room)
        ClusterBuster.evaluate(game)

        return super().get_redirect_url(*args, **kwargs)


class UpdateGame(generic.RedirectView, generic.detail.SingleObjectMixin):
    model = Room
    pattern_name = 'room_detail'
    slug_field = 'code'

    def get_redirect_url(self, *args, **kwargs):
        room = get_object_or_404(Room, code=kwargs['slug'])
        game = Game.objects.filter(room=room).first()
        ClusterBuster.evaluate(game)

        return super().get_redirect_url(*args, **kwargs)


class LeaderHintsFormView(generic.FormView, CheckPlayerView):
    template_name = 'core/leader_hint_form.html'
    form_class = LeaderHintsForm

    def __init__(self):
        self.room = None
        self.game = None
        self.current_player = None
        super().__init__()

    def dispatch(self, request, *args, **kwargs):
        self.room = get_object_or_404(Room, code=kwargs['slug'])
        self.game = Game.objects.filter(room=self.room).first()
        self.current_player = self.get_current_player()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super(LeaderHintsFormView, self).get_context_data(**kwargs)
        room = self.room
        current_player = self.get_current_player()
        if current_player:
            player_data = PlayerContext.load(current_player)
            data.update(player_data)
            player_room_data = Player2RoomContext.load(current_player, room)
            data.update(player_room_data)
        players = room.players.all()
        players_data = list()
        for player in players:
            player_data = PlayerContext.load(player)
            player_room_data = Player2RoomContext.load(player, room)
            player_data.update(player_room_data)
            player_data['is_player'] = player == current_player
            players_data.append(player_data)
        data['players'] = players_data
        teams = room.teams.all()
        teams_data = list()
        for team in teams:
            team_data = TeamContext.load(team)
            if current_player:
                player_team_data = Player2TeamContext.load(current_player, team)
                team_data.update(player_team_data)
            teams_data.append(team_data)
        data['teams'] = teams_data
        return data

    def get_success_url(self):
        room = self.room
        self.success_url = reverse_lazy('update_game', kwargs={'slug': room.code})
        return super().get_success_url()


from django.shortcuts import reverse, redirect
from django.views import generic

from lobbies.models import Player
from .mixins import CheckPlayerView, AssignPlayerView


class PlayerCreate(AssignPlayerView, generic.CreateView):
    model = Player
    fields = ['name']

    def dispatch(self, request, *args, **kwargs):
        player_id = self.request.session.get('player_id')

        if player_id:
            return redirect('player_detail', pk=player_id)
        return super().dispatch(request, *args, **kwargs)


class PlayerUpdate(AssignPlayerView, generic.UpdateView):
    model = Player
    fields = ['name']

    def dispatch(self, request, *args, **kwargs):
        player = self.get_object()

        if not self.is_current_player(player):
            return redirect('player_detail', **kwargs)
        return super().dispatch(request, *args, **kwargs)


class PlayerDetail(generic.DetailView, CheckPlayerView):
    model = Player

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['is_current_player'] = self.is_current_player(self.object)
        return data


class CreatePlayerAndJoinLobby(AssignPlayerView, generic.CreateView):
    model = Player
    fields = ['name']

    def __init__(self):
        super().__init__()
        self.code = None

    def dispatch(self, request, *args, **kwargs):
        self.code = kwargs['slug']
        player = self.get_current_player()

        if player is not None:
            return redirect('lobby_detail', **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        if isinstance(self.object, Player):
            player = self.object
            self.save_player_to_session(player)
            return reverse('join_lobby', kwargs={'slug': self.code})
        return reverse('lobby_detail', kwargs={'slug': self.code})

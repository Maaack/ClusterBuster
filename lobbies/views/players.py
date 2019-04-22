from django.http import HttpResponseRedirect

from django.urls import reverse
from django.views import generic

from lobbies.models import Player
from .mixins import CheckPlayerView, AssignPlayerView


class PlayerCreate(AssignPlayerView, generic.CreateView):
    model = Player
    fields = ['name']

    def dispatch(self, request, *args, **kwargs):
        player_id = self.request.session.get('player_id')

        if player_id:
            return HttpResponseRedirect(reverse('player_detail', kwargs={'pk':player_id}))
        return super(PlayerCreate, self).dispatch(request, *args, **kwargs)


class PlayerUpdate(AssignPlayerView, generic.UpdateView):
    model = Player
    fields = ['name']

    def dispatch(self, request, *args, **kwargs):
        player = self.get_object()

        if not self.is_current_player(player):
            return HttpResponseRedirect(reverse('player_detail', kwargs=kwargs))
        return super(PlayerUpdate, self).dispatch(request, *args, **kwargs)


class PlayerDetail(generic.DetailView, CheckPlayerView):
    model = Player

    def get_context_data(self, **kwargs):
        data = super(PlayerDetail, self).get_context_data(**kwargs)
        data['current_player'] = self.is_current_player(self.object)
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
            return HttpResponseRedirect(reverse('lobby_detail', **kwargs))
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        if isinstance(self.object, Player):
            player = self.object
            self.save_player_to_session(player)
            return reverse('join_lobby', kwargs={'slug': self.code})
        return reverse('lobby_detail', kwargs={'slug': self.code})

from django.shortcuts import reverse, redirect
from django.views import generic

from ..models import Player
from .mixins import CheckPlayerView, AssignPlayerView


class PlayerCreate(AssignPlayerView, generic.CreateView):
    model = Player
    fields = ['name']

    def dispatch(self, request, *args, **kwargs):
        player = self.get_current_player()
        if player:
            return redirect('player_detail', pk=player.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        lobby_code = self.request.POST.get('lobby_code')
        if lobby_code is not None:
            return reverse('join_lobby', kwargs={'slug': lobby_code})
        return super().get_success_url()


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

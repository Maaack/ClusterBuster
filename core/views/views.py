from django.shortcuts import get_object_or_404
from django.views import generic
from django.urls import reverse_lazy

from rooms.models import Room
from games.models import Game
from core.definitions import ClusterBuster

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


class LeaderHintsFormView(generic.FormView):
    template_name = 'core/leader_hint_form.html'
    form_class = LeaderHintsForm

    def __init__(self):
        self.room = None
        super().__init__()

    def dispatch(self, request, *args, **kwargs):
        room = get_object_or_404(Room, code=kwargs['slug'])
        self.room = room
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        room = self.room
        self.success_url = reverse_lazy('update_game', kwargs={'slug': room.code})
        return super().get_success_url()


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
        team = self.get_current_player_team()
        round_number = self.game.get_parameter_value('current_round_count')
        code_numbers = []
        for card_i in range(ClusterBuster.CODE_CARD_SLOTS):
            code_number = self.game.get_parameter_value(('round', round_number, 'team', team, 'code', card_i + 1))
            code_numbers.append(code_number)
        data['code_numbers'] = code_numbers
        return data

    def get_success_url(self):
        room = self.room
        self.success_url = reverse_lazy('update_game', kwargs={'slug': room.code})
        return super().get_success_url()


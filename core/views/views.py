from django.shortcuts import get_object_or_404, redirect
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
        self.player = None
        self.team = None
        self.round_number = 0
        super().__init__()

    def dispatch(self, request, *args, **kwargs):
        self.room = get_object_or_404(Room, code=kwargs['slug'])
        self.game = Game.objects.filter(room=self.room).first()
        self.player = self.get_current_player()
        self.team = self.get_current_player_team()
        self.round_number = self.game.get_parameter_value('current_round_count')
        if not self.is_round_team_leader():
            return redirect('room_detail', slug=kwargs['slug'])
        # TODO: Check if is in leader hint stage
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super(LeaderHintsFormView, self).get_context_data(**kwargs)
        code_numbers = []
        for card_i in range(ClusterBuster.CODE_CARD_SLOTS):
            code_number = self.game.get_parameter_value(('round', self.round_number, 'team', self.team, 'code', card_i + 1))
            code_numbers.append(code_number)
        data['code_numbers'] = code_numbers
        return data

    def get_success_url(self):
        room = self.room
        self.success_url = reverse_lazy('update_game', kwargs={'slug': room.code})
        return super().get_success_url()

    def is_round_team_leader(self):
        if self.player is None:
            return False
        team = self.get_current_player_team()
        if team is None:
            return False
        round_number = self.game.get_parameter_value('current_round_count')
        round_team_leader = self.game.get_parameter_value(('round', round_number, 'team', team, 'leader'))
        return round_team_leader == self.player

    def get_current_player_team(self):
        teams = self.game.get_teams().all()
        for team in teams:
            if team.has_player(self.player):
                return team
        return None

    def form_valid(self, form):
        hints = [form.cleaned_data['hint_1'], form.cleaned_data['hint_2'], form.cleaned_data['hint_3']]
        round_number = self.game.get_parameter_value('current_round_count')
        team = self.get_current_player_team()
        for card_i in range(ClusterBuster.CODE_CARD_SLOTS):
            self.game.set_parameter_value(
                ('round', round_number, 'team', team, 'hint', card_i + 1),
                hints[card_i]
            )
        return super().form_valid(form)

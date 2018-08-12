from django.views.generic import View
from django.views.generic.detail import SingleObjectMixin
from core.models import Player, Game, Team


class CheckPlayerViewMixin(SingleObjectMixin, View):
    class Meta:
        abstract = True

    model = Player

    def is_current_player(self):
        player = self.get_object()
        return self.request.session['player_id'] == player.pk


class AssignPlayerViewMixin(SingleObjectMixin, View):
    class Meta:
        abstract = True

    model = Player

    def assign_player(self):
        player = self.get_object()
        if player:
            self.request.session['player_id'] = player.pk
            self.request.session['player_name'] = player.name
            return True
        return False

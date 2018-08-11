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


class PlayerInGameMixin(SingleObjectMixin, View):
    class Meta:
        abstract = True

    model = Game

    def is_player_in_game(self):
        game = self.get_object()
        if game and self.request.session['player_id'] is not None:
            return game.players.filter(pk=self.request.session['player_id']).exists()
        return False

    def get_player_team(self):
        game = self.get_object()
        if game and self.request.session['player_id'] is not None:
            try:
                return game.teams.get(players__pk=self.request.session['player_id'])
            except Team.DoesNotExist:
                return None
        return None

    def get_player_team_id(self):
        player_team = self.get_player_team()
        if player_team:
            return player_team.pk
        return 0

    def get_context_data(self, **kwargs):
        data = super(PlayerInGameMixin, self).get_context_data(**kwargs)
        data['player_in_game'] = self.is_player_in_game()
        data['player_team_id'] = self.get_player_team_id()
        return data

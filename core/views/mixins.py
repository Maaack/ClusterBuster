from django.views import generic, View
from django.urls import reverse
from core.models import Player, Game, TeamRound


class CheckPlayerView(View):
    class Meta:
        abstract = True

    model = Player

    def is_current_player(self, player):
        return self.get_current_player() == player

    def get_current_player(self):
        player_id = self.request.session.get('player_id')
        if player_id:
            try:
                return Player.objects.get(pk=player_id)
            except Player.DoesNotExist:
                return None


class AssignPlayerView(generic.edit.FormMixin, generic.detail.BaseDetailView):
    class Meta:
        abstract = True

    def assign_player(self, player):
        if type(player) is Player:
            self.request.session['player_id'] = player.pk
            self.request.session['player_name'] = player.name

    def form_valid(self, form):
        self.request.session.save()
        form.instance.session_id = self.request.session.session_key
        return super(AssignPlayerView, self).form_valid(form)

    def get_success_url(self):
        if type(self.object) is Player:
            player = self.object
            self.assign_player(player)
            return reverse('player_detail', kwargs={'pk': self.object.pk})
        return reverse('player_list')


class ContextData(object):
    @staticmethod
    def get_game_data(game):
        """
        :param game: Game
        :return: dict
        """
        data = dict()
        data['game'] = game
        data['current_round'] = game.get_current_round()
        return data

    @staticmethod
    def get_player_data(player, game):
        """
        :param player: Player
        :param game: Game
        :return: dict
        """
        data = dict()
        data['player'] = player
        has_player = game.has_player(player)
        team = game.get_player_team(player)
        data['player_in_game'] = has_player
        data['player_team'] = team
        data['player_team_round'] = None
        data['player_team_round_leader'] = None
        data['player_is_current_leader'] = None
        if has_player and team:
            data['player_team_round'] = team.current_team_round
        if team and team.current_team_round:
            round_leader = team.current_team_round.leader
            data['player_team_round_leader'] = round_leader
            data['player_is_current_leader'] = round_leader == player
        return data

    @staticmethod
    def get_hint_data(team_round):
        """
        :param team_round: TeamRound
        :return: dict
        """
        data = dict()
        team_round_words = team_round.team_round_words.all()
        data['words'] = [
            {'text': team_round_word.team_word.word.text, 'position': team_round_word.team_word.position} for
            team_round_word in team_round_words]
        return data

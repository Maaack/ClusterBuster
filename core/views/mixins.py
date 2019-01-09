from django.views import generic, View
from django.urls import reverse
from core.models import Player, Game, TeamRound
from core.models.interface import PlayerGameInterface


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


class AssignPlayerView(generic.edit.FormMixin, View):
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


class ContextDataLoader(object):
    @staticmethod
    def get_game_data(game):
        """
        :param game: Game
        :return: dict
        """
        data = dict()
        data['game'] = game
        data['round'] = game.current_round
        return data

    @staticmethod
    def get_player_data(player, game):
        """
        :param player: Player
        :param game: Game
        :return: dict
        """
        player_game_interface = PlayerGameInterface(player, game)
        data = dict()
        data['player'] = player
        has_player = player_game_interface.has_player()
        team = player_game_interface.get_team()
        data['player_in_game'] = has_player
        data['player_team'] = team
        data['player_team_round'] = None
        data['player_team_round_leader'] = None
        data['is_leader'] = None
        if has_player and team and team.current_team_round:
            team_round = team.current_team_round
            round_leader = team.current_team_round.leader
            is_leader = round_leader == player
            data['player_team_round'] = team_round
            data['player_team_round_leader'] = round_leader
            data['is_leader'] = is_leader
            data.update(ContextDataLoader.get_round_hints_data(game.teams.all(), team))
            if is_leader:
                data.update(ContextDataLoader.get_round_leader_word_data(team_round))
        return data

    @staticmethod
    def get_round_hints_data(teams, player_team):
        """
        :param team_round: TeamRound
        :return: dict
        """
        data = dict()
        for team in teams:
            target_words = team.current_team_round.target_words.order_by('order').all()
            target_words_dict = [
                {'hint': target_word.get_hint_text(), 'order': target_word.order + 1} for
                target_word in target_words]
            if team == player_team:
                data['team_hints'] = target_words_dict
            else:
                data['opponent_team_hints'] = target_words_dict
        return data

    @staticmethod
    def get_round_leader_word_data(team_round):
        """
        :param team_round: TeamRound
        :return: dict
        """
        data = dict()
        target_words = team_round.target_words.all()
        data['words'] = [
            {'text': target_word.team_word.word.text, 'position': target_word.team_word.position} for
            target_word in target_words]
        return data

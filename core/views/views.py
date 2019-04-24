from django.shortcuts import get_object_or_404, redirect, reverse
from django.views import generic

from lobbies.views.mixins import CheckPlayerView
from lobbies.models import Lobby, Player, Team

from ..models import State, ClusterBuster
from .forms import LeaderHintsForm, PlayerGuessForm


class StartGame(generic.RedirectView, generic.detail.SingleObjectMixin):
    model = Lobby
    pattern_name = 'lobby_detail'
    slug_field = 'code'

    def get_redirect_url(self, *args, **kwargs):
        lobby = get_object_or_404(Lobby, code=kwargs['slug'])
        game = ClusterBuster.objects.create()
        game.setup("cluster_buster", lobby=lobby)
        game.start()
        game.update()
        return super().get_redirect_url(*args, **kwargs)


class UpdateGame(generic.RedirectView, generic.detail.SingleObjectMixin):
    model = ClusterBuster
    context_object_name = 'game'
    pattern_name = 'game_detail'
    slug_field = 'code'

    def get_redirect_url(self, *args, **kwargs):
        game = get_object_or_404(ClusterBuster, code=kwargs['slug'])
        game.update()
        return super().get_redirect_url(*args, **kwargs)


class GameViewAbstract(CheckPlayerView):
    class Meta:
        abstract = True

    def __init__(self):
        self.game = None
        self.player = None
        self.team = None
        self.opponent_team = None
        self.round_number = 0
        super().__init__()

    def dispatch(self, request, *args, **kwargs):
        self.game = get_object_or_404(ClusterBuster, code=kwargs['slug'])
        self.player = self.get_current_player()
        if self.player is None:
            return redirect('lobby_detail', slug=self.game.lobby.code)
        self.team = self.get_current_player_team()
        if self.team is None:
            return redirect('lobby_detail', slug=self.game.lobby.code)
        self.opponent_team = self.get_current_player_opponent_team()
        if self.opponent_team is None:
            return redirect('lobby_detail', slug=self.game.lobby.code)
        self.round_number = self.game.get_parameter_value('current_round_number')
        return super().dispatch(request, *args, **kwargs)

    def get_current_player_team(self):
        teams = self.game.teams.all()
        for team in teams:
            if team.has_player(self.player):
                return team
        return None

    def get_current_player_opponent_team(self):
        teams = self.game.teams.all()
        for team in teams:
            if not team.has_player(self.player):
                return team
        return None

    def get_secret_words_data(self):
        secret_words = []
        for word_i in range(ClusterBuster.SECRET_WORDS_PER_TEAM):
            secret_word_number = word_i + 1
            secret_word = self.game.get_parameter_value(('team', self.team, 'secret_word', secret_word_number))
            secret_words.append(str(secret_word))
        return secret_words

    def get_tokens_data(self):
        tokens = {}
        team_winning_tokens = self.game.get_parameter_value(('team_winning_tokens', self.team))
        team_losing_tokens = self.game.get_parameter_value(('team_losing_tokens', self.team))
        tokens['player'] = {
            'name': self.team.name,
            'winning_tokens': team_winning_tokens,
            'losing_tokens': team_losing_tokens,
        }
        team_winning_tokens = self.game.get_parameter_value(('team_winning_tokens', self.opponent_team))
        team_losing_tokens = self.game.get_parameter_value(('team_losing_tokens', self.opponent_team))
        tokens['opponent'] = {
            'name': self.opponent_team.name,
            'winning_tokens': team_winning_tokens,
            'losing_tokens': team_losing_tokens,
        }
        return tokens

    def get_round_guesses_data(self):
        fsm2 = self.game.get_parameter_value('fsm2')  # type: State
        is_first_round = fsm2.slug == 'first_round'
        guesses = {}
        for guessing_team in self.game.teams.all():  # type: Team
            guesses[guessing_team.name] = {}
            for hinting_team in self.game.teams.all():  # type: Team
                if guessing_team != hinting_team and is_first_round:
                    continue
                guesses[guessing_team.name][hinting_team.name] = []
                for card_i in range(ClusterBuster.CODE_CARD_SLOTS):
                    hint_number = card_i + 1
                    hint = self.game.get_parameter_value(
                        ('round', self.round_number, 'team', hinting_team, 'hint', hint_number),
                    )
                    guess = self.game.get_parameter_value(
                        ('round', self.round_number, 'guessing_team', guessing_team, 'hinting_team', hinting_team,
                         'guess',
                         hint_number),
                    )
                    guesses[guessing_team.name][hinting_team.name].append(
                        {"hint_number": hint_number, "hint": hint, "guess": guess})
        return guesses

    def get_round_hints_data(self):
        hints = {}
        for team in self.game.teams.all():  # type: Team
            hints[team.name] = []
            for card_i in range(ClusterBuster.CODE_CARD_SLOTS):
                hint_number = card_i + 1
                hint = self.game.get_parameter_value(
                    ('round', self.round_number, 'team', team, 'hint', hint_number),
                )
                hints[team.name].append(
                    {"hint_number": hint_number, "hint": hint})
        return hints

    def get_game_logs_data(self):
        game_logs = {}
        last_round_number = self.round_number - 1
        for team in self.game.teams.all():  # type: Team
            game_logs[team.name] = {}
            rounds = []
            words = ["?"] * ClusterBuster.SECRET_WORDS_PER_TEAM
            if team == self.team:
                for word_i in range(len(words)):
                    secret_word_number = word_i + 1
                    secret_word = self.game.get_parameter_value(('team', self.team, 'secret_word', secret_word_number))
                    words[word_i] = str(secret_word)
            game_logs[team.name]["words"] = words
            for round_i in range(last_round_number):
                round_number = round_i + 1
                hints = [None] * ClusterBuster.SECRET_WORDS_PER_TEAM
                for card_i in range(ClusterBuster.CODE_CARD_SLOTS):
                    hint_number = card_i + 1
                    code_number = self.game.get_parameter_value(
                        ('round', round_number, 'team', team, 'code', hint_number))
                    hint = self.game.get_parameter_value(
                        ('round', round_number, 'team', team, 'hint', hint_number),
                    )
                    code_number_index = code_number - 1
                    hints[code_number_index] = hint
                rounds.append(hints)
            game_logs[team.name]["rounds"] = rounds
        return game_logs

    def is_round_team_leader(self):
        if self.player is None or self.team is None:
            return False
        round_team_leader = self.game.get_parameter_value(('round', self.round_number, 'team', self.team, 'leader'))
        return round_team_leader == self.player


class GameDetail(generic.DetailView, GameViewAbstract):
    model = ClusterBuster
    context_object_name = 'game'
    slug_field = 'code'
    template_name = 'core/game_detail.html'

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        self.game.update()
        return response

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        show_leader_hints_form_link = False
        show_player_guesses_form_link = False
        show_player_guesses_opponents_form_link = False
        show_score_teams_link = False
        show_start_next_round_link = False
        show_guesses_information = False
        show_hints_information = False
        winning_team = None
        losing_team = None
        round_hints = []
        round_guesses = []
        fsm0 = self.game.get_parameter_value('fsm0')  # type: State
        is_game_over = fsm0.slug == 'game_over'
        if is_game_over:
            winning_team = self.game.get_parameter_value('game_winning_team')
            losing_team = self.game.get_parameter_value('game_losing_team')
        else:
            fsm2 = self.game.get_parameter_value('fsm2')  # type: State
            is_first_round = fsm2.slug == 'first_round'
            fsm3 = self.game.get_parameter_value('fsm3')  # type: State
            fsm3_state = fsm3.slug
            if fsm3_state == 'leaders_make_hints_stage' and self.is_round_team_leader():
                show_leader_hints_form_link = True
            elif fsm3_state == 'teams_guess_codes_stage':
                round_hints = self.get_round_hints_data()
                show_hints_information = True
                if not self.is_round_team_leader():
                    show_player_guesses_form_link = True
                if not is_first_round:
                    show_player_guesses_opponents_form_link = True
            elif fsm3_state == 'score_teams_stage' and self.is_round_team_leader():
                show_start_next_round_link = True
            elif fsm3_state == 'teams_share_guesses_stage':
                round_guesses = self.get_round_guesses_data()
                show_guesses_information = True
                show_score_teams_link = True
        data['show_leader_hints_form_link'] = show_leader_hints_form_link
        data['show_player_guesses_form_link'] = show_player_guesses_form_link
        data['show_player_guesses_opponents_form_link'] = show_player_guesses_opponents_form_link
        data['winning_team'] = winning_team
        data['losing_team'] = losing_team
        data['is_game_over'] = is_game_over
        data['show_start_next_round_link'] = show_start_next_round_link
        data['show_hints_information'] = show_hints_information
        data['show_guesses_information'] = show_guesses_information
        data['show_score_teams_link'] = show_score_teams_link
        data['secret_words'] = self.get_secret_words_data()
        data['game_logs'] = self.get_game_logs_data()
        data['round_number'] = self.round_number
        data['round_hints'] = round_hints
        data['round_guesses'] = round_guesses
        data['is_round_leader'] = self.is_round_team_leader()
        data['tokens'] = self.get_tokens_data()
        fsm3 = self.game.get_parameter_value('fsm3')
        data['round_stage'] = fsm3.name
        return data


class GameFormAbstractView(generic.FormView, GameViewAbstract):
    class Meta:
        abstract = True

    def get_success_url(self):
        return reverse('game_detail', kwargs={'slug': self.game.code})

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['game'] = self.game
        return data


class LeaderHintsFormView(GameFormAbstractView):
    template_name = 'core/leader_hint_form.html'
    form_class = LeaderHintsForm

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if not self.is_round_team_leader():
            return redirect('game_detail', slug=kwargs['slug'])
        fsm3 = self.game.get_parameter_value('fsm3')  # type: State
        if fsm3.slug != 'leaders_make_hints_stage':
            return redirect('game_detail', slug=kwargs['slug'])
        return response

    def get_context_data(self, **kwargs):
        data = super(LeaderHintsFormView, self).get_context_data(**kwargs)
        code_numbers = []
        code_words = []
        for card_i in range(ClusterBuster.CODE_CARD_SLOTS):
            code_number = self.game.get_parameter_value(
                ('round', self.round_number, 'team', self.team, 'code', card_i + 1))
            code_numbers.append(code_number)
            secret_word = self.game.get_parameter_value(('team', self.team, 'secret_word', code_number))
            code_words.append(str(secret_word))
        data['code_numbers'] = code_numbers
        data['code_words'] = code_words
        return data

    def get_initial(self):
        initial_data = super().get_initial()
        hint_keys = ['hint_1', 'hint_2', 'hint_3']
        for card_i in range(ClusterBuster.CODE_CARD_SLOTS):
            current_hint = self.game.get_parameter_value(
                ('round', self.round_number, 'team', self.team, 'hint', card_i + 1))
            if current_hint is None:
                code_number = self.game.get_parameter_value(
                    ('round', self.round_number, 'team', self.team, 'code', card_i + 1))
                current_hint = self.game.get_parameter_value(('team', self.team, 'secret_word', code_number))
            initial_data[hint_keys[card_i]] = str(current_hint)
        return initial_data

    def form_valid(self, form):
        hints = [form.cleaned_data['hint_1'], form.cleaned_data['hint_2'], form.cleaned_data['hint_3']]
        for card_i in range(ClusterBuster.CODE_CARD_SLOTS):
            self.game.set_parameter_value(
                ('round', self.round_number, 'team', self.team, 'hint', card_i + 1),
                hints[card_i]
            )
        self.game.update()
        return super().form_valid(form)


class PlayerGuessesFormView(GameFormAbstractView):
    template_name = 'core/player_guess_form.html'
    form_class = PlayerGuessForm

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        # TODO: Check if player is leader guessing own hints. Currently not letting leaders guess on any hints
        if self.is_round_team_leader():
            return redirect('game_detail', slug=kwargs['slug'])
        fsm3 = self.game.get_parameter_value('fsm3')  # type: State
        if fsm3.slug != 'teams_guess_codes_stage':
            return redirect('game_detail', slug=kwargs['slug'])
        return response

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        hints = []
        secret_words = []
        for card_i in range(ClusterBuster.CODE_CARD_SLOTS):
            hint = self.game.get_parameter_value(
                ('round', self.round_number, 'team', self.team, 'hint', card_i + 1)
            )
            hints.append(hint)
        for word_i in range(ClusterBuster.SECRET_WORDS_PER_TEAM):
            secret_word_num = word_i + 1
            secret_word = self.game.get_parameter_value(('team', self.team, 'secret_word', secret_word_num))
            secret_words.append({secret_word_num: secret_word})
        data['hints'] = hints
        data['secret_words'] = secret_words
        return data

    def form_valid(self, form):
        guesses = [form.cleaned_data['guess_1'], form.cleaned_data['guess_2'], form.cleaned_data['guess_3']]
        for card_i in range(ClusterBuster.CODE_CARD_SLOTS):
            self.game.set_parameter_value(
                (
                    'round', self.round_number, 'guessing_team', self.team, 'hinting_team', self.team, 'guess',
                    card_i + 1),
                guesses[card_i]
            )
        self.game.update()
        return super().form_valid(form)


class PlayerGuessesOpponentHintsFormView(GameFormAbstractView):
    template_name = 'core/player_guess_form.html'
    form_class = PlayerGuessForm

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        fsm3 = self.game.get_parameter_value('fsm3')  # type: State
        if fsm3.slug != 'teams_guess_codes_stage':
            return redirect('game_detail', slug=kwargs['slug'])
        return response

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        hints = []
        for card_i in range(ClusterBuster.CODE_CARD_SLOTS):
            hint = self.game.get_parameter_value(
                ('round', self.round_number, 'team', self.opponent_team, 'hint', card_i + 1)
            )
            hints.append(hint)
        data['hints'] = hints
        return data

    def form_valid(self, form):
        guesses = [form.cleaned_data['guess_1'], form.cleaned_data['guess_2'], form.cleaned_data['guess_3']]
        for card_i in range(ClusterBuster.CODE_CARD_SLOTS):
            self.game.set_parameter_value(
                (
                    'round', self.round_number, 'guessing_team', self.team, 'hinting_team', self.opponent_team, 'guess',
                    card_i + 1),
                guesses[card_i]
            )
        self.game.update()
        return super().form_valid(form)


class StartNextRound(generic.RedirectView, generic.detail.SingleObjectMixin, GameViewAbstract):
    model = ClusterBuster
    context_object_name = 'game'
    pattern_name = 'game_detail'
    slug_field = 'code'

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if not self.is_round_team_leader():
            return redirect('game_detail', slug=kwargs['slug'])
        fsm3 = self.game.get_parameter_value('fsm3')  # type: State
        if fsm3.slug != 'score_teams_stage':
            return redirect('game_detail', slug=kwargs['slug'])
        return response

    def get_redirect_url(self, *args, **kwargs):
        game = get_object_or_404(ClusterBuster, code=kwargs['slug'])
        game.start_next_round()
        game.update()

        return super().get_redirect_url(*args, **kwargs)


class ScoreTeams(generic.RedirectView, generic.detail.SingleObjectMixin, GameViewAbstract):
    model = ClusterBuster
    context_object_name = 'game'
    pattern_name = 'game_detail'
    slug_field = 'code'

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if not self.is_round_team_leader():
            return redirect('game_detail', slug=kwargs['slug'])
        fsm3 = self.game.get_parameter_value('fsm3')  # type: State
        if fsm3.slug != 'teams_share_guesses_stage':
            return redirect('game_detail', slug=kwargs['slug'])
        return response

    def get_redirect_url(self, *args, **kwargs):
        game = get_object_or_404(ClusterBuster, code=kwargs['slug'])
        game.score_teams()
        game.update()
        return super().get_redirect_url(*args, **kwargs)

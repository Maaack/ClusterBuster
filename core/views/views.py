from django.shortcuts import get_object_or_404, redirect, reverse
from django.views import generic

from rooms.models import Room, Player, Team
from games.models import Game, StateMachine
from core.definitions import ClusterBuster

from rooms.views.mixins import CheckPlayerView

from .forms import LeaderHintsForm, PlayerGuessForm


class StartGame(generic.RedirectView, generic.detail.SingleObjectMixin):
    model = Room
    pattern_name = 'room_detail'
    slug_field = 'code'

    def get_redirect_url(self, *args, **kwargs):
        room = get_object_or_404(Room, code=kwargs['slug'])
        game = Game.objects.create()
        game.setup("cluster_buster", room=room)
        game.start(ClusterBuster)
        game.update(ClusterBuster)

        return super().get_redirect_url(*args, **kwargs)


class UpdateGame(generic.RedirectView, generic.detail.SingleObjectMixin):
    model = Game
    pattern_name = 'game_detail'
    slug_field = 'code'

    def get_redirect_url(self, *args, **kwargs):
        game = get_object_or_404(Game, code=kwargs['slug'])
        game.update(ClusterBuster)

        return super().get_redirect_url(*args, **kwargs)


class GameViewAbstract(CheckPlayerView):
    class Meta:
        abstract = True

    def __init__(self):
        self.game = None
        self.player = None
        self.team = None
        self.round_number = 0
        super().__init__()

    def dispatch(self, request, *args, **kwargs):
        self.game = get_object_or_404(Game, code=kwargs['slug'])
        self.player = self.get_current_player()
        if self.player is None:
            return redirect('room_detail', slug=self.game.room.code)
        self.team = self.get_current_player_team()
        if self.team is None:
            return redirect('room_detail', slug=self.game.room.code)
        self.round_number = self.game.get_parameter_value('current_round_number')
        return super().dispatch(request, *args, **kwargs)

    def get_current_player_team(self):
        teams = self.game.teams.all()
        for team in teams:
            if team.has_player(self.player):
                return team
        return None

    def get_secret_words_data(self):
        secret_words = []
        for word_i in range(ClusterBuster.SECRET_WORDS_PER_TEAM):
            secret_word_number = word_i + 1
            secret_word = self.game.get_parameter_value(('team', self.team, 'secret_word', secret_word_number))
            secret_words.append(str(secret_word))
        return secret_words

    def get_all_guesses_data(self):
        fsm2 = self.game.get_parameter_value('fsm2')  # type: StateMachine
        is_first_round = fsm2.current_state.slug == 'first_round'
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

    def is_round_team_leader(self):
        if self.player is None or self.team is None:
            return False
        round_team_leader = self.game.get_parameter_value(('round', self.round_number, 'team', self.team, 'leader'))
        return round_team_leader == self.player


class GameDetail(generic.DetailView, GameViewAbstract):
    model = Game
    slug_field = 'code'
    template_name = 'core/game_detail.html'

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        self.game.update(ClusterBuster)
        return response

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        show_leader_hints_form_link = False
        show_player_guesses_form_link = False
        show_start_next_round_link = False
        show_guesses_information = False
        all_guesses = []
        fsm3 = self.game.get_parameter_value('fsm3')  # type: StateMachine
        fsm3_state = fsm3.current_state.slug
        if fsm3_state == 'leaders_make_hints_stage' and self.is_round_team_leader():
            show_leader_hints_form_link = True
        elif fsm3_state == 'teams_guess_codes_stage' and not self.is_round_team_leader():
            show_player_guesses_form_link = True
        elif fsm3_state == 'score_teams_stage' and self.is_round_team_leader():
            show_start_next_round_link = True
        elif fsm3_state == 'teams_share_guesses_stage':
            all_guesses = self.get_all_guesses_data()
            show_guesses_information = True
        data['show_leader_hints_form_link'] = show_leader_hints_form_link
        data['show_player_guesses_form_link'] = show_player_guesses_form_link
        data['show_start_next_round_link'] = show_start_next_round_link
        data['show_guesses_information'] = show_guesses_information
        data['secret_words'] = self.get_secret_words_data()
        data['round_number'] = self.round_number
        data['all_guesses'] = all_guesses
        data['is_round_leader'] = self.is_round_team_leader()
        fsm3 = self.game.get_parameter_value('fsm3')  # type: StateMachine
        data['round_stage'] = fsm3.current_state.name
        return data


class GameFormAbstractView(generic.FormView, GameViewAbstract):
    class Meta:
        abstract = True

    def get_success_url(self):
        return reverse('game_detail', kwargs={'slug': self.game.code})


class LeaderHintsFormView(GameFormAbstractView):
    template_name = 'core/leader_hint_form.html'
    form_class = LeaderHintsForm

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if not self.is_round_team_leader():
            return redirect('game_detail', slug=kwargs['slug'])
        fsm3 = self.game.get_parameter_value('fsm3')  # type: StateMachine
        if fsm3.current_state.slug != 'leaders_make_hints_stage':
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
        self.game.update(ClusterBuster)
        return super().form_valid(form)


class PlayerGuessesFormView(GameFormAbstractView):
    template_name = 'core/player_guess_form.html'
    form_class = PlayerGuessForm

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        # TODO: Check if player is leader guessing own hints. Currently not letting leaders guess on any hints
        if self.is_round_team_leader():
            return redirect('game_detail', slug=kwargs['slug'])
        fsm3 = self.game.get_parameter_value('fsm3')  # type: StateMachine
        if fsm3.current_state.slug != 'teams_guess_codes_stage':
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
        self.game.update(ClusterBuster)
        return super().form_valid(form)


class StartNextRound(generic.RedirectView, generic.detail.SingleObjectMixin, GameViewAbstract):
    model = Game
    pattern_name = 'game_detail'
    slug_field = 'code'

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if not self.is_round_team_leader():
            return redirect('game_detail', slug=kwargs['slug'])
        fsm3 = self.game.get_parameter_value('fsm3')  # type: StateMachine
        if fsm3.current_state.slug != 'score_teams_stage':
            return redirect('game_detail', slug=kwargs['slug'])
        return response

    def get_redirect_url(self, *args, **kwargs):
        game = get_object_or_404(Game, code=kwargs['slug'])
        start_next_round_method = ClusterBuster.method_map('start_next_round')
        start_next_round_method(game)
        game.update(ClusterBuster)

        return super().get_redirect_url(*args, **kwargs)

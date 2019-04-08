from django.shortcuts import get_object_or_404, redirect, reverse
from django.views import generic

from rooms.models import Room
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
    model = Room
    pattern_name = 'room_detail'
    slug_field = 'code'

    def get_redirect_url(self, *args, **kwargs):
        room = get_object_or_404(Room, code=kwargs['slug'])
        game = Game.objects.filter(room=room).first()
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
        self.round_number = self.game.get_parameter_value('current_round_count')
        return super().dispatch(request, *args, **kwargs)

    def get_current_player_team(self):
        teams = self.game.teams.all()
        for team in teams:
            if team.has_player(self.player):
                return team
        return None


class GameDetail(generic.DetailView, GameViewAbstract):
    model = Game
    slug_field = 'code'
    template_name = 'core/game_detail.html'

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        self.game.update(ClusterBuster)
        return response


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
            return redirect('room_detail', slug=kwargs['slug'])
        fsm3 = self.game.get_parameter_value('fsm3')  # type: StateMachine
        if fsm3.current_state.slug != 'leaders_make_hints_stage':
            return redirect('room_detail', slug=kwargs['slug'])
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

    def is_round_team_leader(self):
        if self.player is None or self.team is None:
            return False
        round_team_leader = self.game.get_parameter_value(('round', self.round_number, 'team', self.team, 'leader'))
        return round_team_leader == self.player

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
            return redirect('room_detail', slug=kwargs['slug'])
        fsm3 = self.game.get_parameter_value('fsm3')  # type: StateMachine
        if fsm3.current_state.slug != 'teams_guess_codes_stage':
            return redirect('room_detail', slug=kwargs['slug'])
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

    def is_round_team_leader(self):
        if self.player is None or self.team is None:
            return False
        round_team_leader = self.game.get_parameter_value(('round', self.round_number, 'team', self.team, 'leader'))
        return round_team_leader == self.player

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

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import loader
from django.urls import reverse
from django.views import generic
from extra_views import ModelFormSetView

from core.models import Game, GameRoom, Player, TargetWord, LeaderHint, PlayerGuess
from .mixins import CheckPlayerView, AssignPlayerView, ContextDataLoader


# Create your views here.
def index(request):
    template = loader.get_template('core/index.html')
    return HttpResponse(template.render({}, request))


class GameCreate(generic.CreateView):
    model = Game
    fields = []

    def form_valid(self, form):
        self.request.session.save()
        form.instance.session_id = self.request.session.session_key
        return super(GameCreate, self).form_valid(form)

    def get_success_url(self):
        return reverse('game_detail', kwargs={'pk': self.object.pk})


class GameList(generic.ListView):
    context_object_name = 'latest_games'

    def get_queryset(self):
        return Game.objects.order_by('-created')[:5]


class GameNextRound(generic.RedirectView, generic.detail.SingleObjectMixin):
    model = GameRoom
    pattern_name = 'gameroom_detail'
    slug_field = 'code'

    def get_redirect_url(self, *args, **kwargs):
        game = get_object_or_404(Game, gameroom__code=kwargs['slug'])
        game.next_round()

        return super().get_redirect_url(*args, **kwargs)


class GameDetail(generic.DetailView):
    model = Game


class GameRoomList(generic.ListView):
    context_object_name = 'game_room_list'

    def get_queryset(self):
        return GameRoom.active.all()


class GameRoomDetail(generic.DetailView):
    model = GameRoom
    slug_field = 'code'

    def __init__(self):
        super(GameRoomDetail, self).__init__()
        self.game = None

    def get_queryset(self):
        return GameRoom.active.all()

    def dispatch(self, request, *args, **kwargs):
        self.game = self.get_object().game
        return super(GameRoomDetail, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super(GameRoomDetail, self).get_context_data(**kwargs)
        data.update(ContextDataLoader.get_game_data(self.game))
        player_id = self.request.session.get('player_id')
        if player_id:
            player = get_object_or_404(Player, pk=player_id)
            data.update(ContextDataLoader.get_player_data(player, self.game))
        return data


class PlayerCreate(AssignPlayerView, generic.CreateView):
    model = Player
    fields = ['name']

    def dispatch(self, request, *args, **kwargs):
        player_id = self.request.session.get('player_id')

        if player_id:
            return HttpResponseRedirect(reverse('player_detail', kwargs={'pk':player_id}))
        return super(PlayerCreate, self).dispatch(request, *args, **kwargs)


class PlayerUpdate(AssignPlayerView, CheckPlayerView, generic.UpdateView):
    model = Player
    fields = ['name']

    def dispatch(self, request, *args, **kwargs):
        player = self.get_object()

        if not self.is_current_player(player):
            return HttpResponseRedirect(reverse('player_detail', kwargs=kwargs))
        return super(PlayerUpdate, self).dispatch(request, *args, **kwargs)


class PlayerDetail(generic.DetailView, CheckPlayerView):
    model = Player

    def get_context_data(self, **kwargs):
        data = super(PlayerDetail, self).get_context_data(**kwargs)
        data['current_player'] = self.is_current_player(self.object)
        return data


class PlayerJoinGame(generic.RedirectView, generic.detail.SingleObjectMixin):
    model = GameRoom
    pattern_name = 'gameroom_detail'
    slug_field = 'code'

    def get_redirect_url(self, *args, **kwargs):
        player_id = self.request.session.get('player_id')

        if player_id:
            player = get_object_or_404(Player, pk=player_id)
            game = get_object_or_404(Game, gameroom__code=kwargs['slug'])
            game.join(player)

        return super().get_redirect_url(*args, **kwargs)


class GenericTeamRoundFormView(generic.FormView):
    class Meta:
        abstract = True

    def __init__(self):
        super(GenericTeamRoundFormView, self).__init__()
        self.game_room = None
        self.game = None
        self.player = None
        self.current_round = None
        self.current_team_round = None

    def dispatch(self, request, *args, **kwargs):
        game_room_code = kwargs['slug']
        self.game_room = get_object_or_404(GameRoom, code=game_room_code)
        self.game = self.game_room.game
        self.current_round = self.game.current_round
        player_id = self.request.session.get('player_id')
        self.player = get_object_or_404(Player, pk=player_id)
        self.current_team_round = self.player.get_game_team(self.game).current_team_round
        return super(GenericTeamRoundFormView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super(GenericTeamRoundFormView, self).get_context_data(**kwargs)
        data.update(ContextDataLoader.get_game_data(self.game))
        data.update(ContextDataLoader.get_player_data(self.player, self.game))
        return data

    def get_success_url(self):
        return reverse('gameroom_detail', kwargs={'slug': self.game_room.code})


class LeaderHintFormSetView(ModelFormSetView, GenericTeamRoundFormView):
    model = LeaderHint
    fields = ['hint']
    factory_kwargs = {
        'extra': 0,
    }

    def get_queryset(self):
        return LeaderHint.objects.filter(target_word__team_round=self.current_team_round)

    def formset_valid(self, formset):
        response = super(LeaderHintFormSetView, self).formset_valid(formset)
        self.current_team_round.advance_stage()
        self.current_team_round.round.advance_stage()
        return response


class PlayerGuessFormSetView(GenericTeamRoundFormView):

    def __init__(self):
        super(PlayerGuessFormSetView, self).__init__()
        self.all_target_words = None

    def dispatch(self, request, *args, **kwargs):
        result = super(PlayerGuessFormSetView, self).dispatch(request, *args, **kwargs)
        self.all_target_words = TargetWord.objects.filter(team_round__round=self.current_round).all()
        for word in self.all_target_words:
            PlayerGuess.objects.update_or_create(player=self.player, target_word=word)
        return result

    def get_queryset(self):
        return PlayerGuess.objects.filter(player=self.player)

    def get_guess(self):
        return PlayerGuess.objects.filter(player=self.player)

    def get_context_data(self, **kwargs):
        data = super(PlayerGuessFormSetView, self).get_context_data(**kwargs)
        return data

    def formset_valid(self, formset):
        pass
        # response = super(PlayerGuessFormSetView, self).formset_valid(formset)
        # if all teammates have submitted guesses and they agree
        # create a team guess
        # self.team_round.advance_stage()
        # self.team_round.round.advance_stage()
        # return response


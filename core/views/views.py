from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.views import generic
from django.urls import reverse
from core.models import Game, GameRoom, Player, TeamRoundWord
from extra_views import ModelFormSetView
from .mixins import CheckPlayerView, AssignPlayerView, ContextData


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
        data.update(ContextData.get_game_data(self.game))
        player_id = self.request.session.get('player_id')
        if player_id:
            player = get_object_or_404(Player, pk=player_id)
            data.update(ContextData.get_player_data(player, self.game))
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


class TeamRoundWordFormSetView(ModelFormSetView):
    model = TeamRoundWord
    fields = ['hint']
    factory_kwargs = {
        'extra': 0,
    }

    def __init__(self):
        super(TeamRoundWordFormSetView, self).__init__()
        self.game_room = None
        self.game = None
        self.player = None
        self.team_round = None

    def get_queryset(self):
        return TeamRoundWord.objects.filter(team_round=self.team_round)

    def dispatch(self, request, *args, **kwargs):
        game_room_code = kwargs['slug']
        self.game_room = get_object_or_404(GameRoom, code=game_room_code)
        self.game = self.game_room.game
        player_id = self.request.session.get('player_id')
        self.player = get_object_or_404(Player, pk=player_id)
        self.team_round = self.player.get_game_team(self.game).current_team_round
        return super(TeamRoundWordFormSetView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super(TeamRoundWordFormSetView, self).get_context_data(**kwargs)
        data.update(ContextData.get_game_data(self.game))
        data.update(ContextData.get_player_data(self.player, self.game))
        if data['player_is_current_leader']:
            data.update(ContextData.get_round_leader_word_data(self.team_round))
        return data

    def formset_valid(self, formset):
        response = super(TeamRoundWordFormSetView, self).formset_valid(formset)
        self.team_round.advance_stage()
        self.team_round.round.advance_stage()
        return response

    def get_success_url(self):
        return reverse('gameroom_detail', kwargs={'slug': self.game_room.code})


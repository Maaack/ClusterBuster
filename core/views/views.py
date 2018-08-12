from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.views import generic
from django.urls import reverse
from django.core.exceptions import MultipleObjectsReturned

from core.models import Game, GameRoom, Player
from .mixins import CheckPlayerView, AssignPlayerView


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
    context_object_name = 'latest_game_list'

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

    def get_queryset(self):
        return GameRoom.active.all()

    def get_context_data(self, **kwargs):
        data = super(GameRoomDetail, self).get_context_data(**kwargs)
        game = self.get_object().game
        # Round current_round
        current_round = game.get_current_round()
        data['game'] = game
        data['current_round'] = current_round
        player_id = self.request.session.get('player_id')

        if player_id:
            player = get_object_or_404(Player, pk=player_id)
            data['player'] = player
            data['player_in_game'] = game.has_player(player)
            data['player_team'] = game.get_player_team(player)
            data['player_is_current_leader'] = current_round.is_leader(player)

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



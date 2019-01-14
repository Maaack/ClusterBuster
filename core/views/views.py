from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import loader
from django.urls import reverse
from django.views import generic
from extra_views import ModelFormSetView

from core.models import Room, Game, Player, TargetWord, LeaderHint, PlayerGuess
from core import interfaces
from .contexts import RoomContext, PlayerRoomContext, ContextDataLoader
from .mixins import CheckPlayerView, AssignPlayerView
from .forms import HintForm, GuessForm, OpponentGuessForm


# Create your views here.
def index(request):
    template = loader.get_template('core/index.html')
    return HttpResponse(template.render({}, request))


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


class RoomCreate(generic.CreateView):
    model = Room
    fields = []

    def form_valid(self, form):
        self.request.session.save()
        form.instance.session_id = self.request.session.session_key
        response = super(RoomCreate, self).form_valid(form)
        interfaces.RoomInterface(self.object).setup()
        return response

    def get_success_url(self):
        return reverse('room_detail', kwargs={'slug': self.object.code})


class RoomList(generic.ListView):
    context_object_name = 'active_rooms'

    def get_queryset(self):
        return Room.active_rooms.all()


class RoomDetail(generic.DetailView):
    model = Room
    slug_field = 'code'

    def __init__(self):
        super(RoomDetail, self).__init__()
        self.game = None

    def get_queryset(self):
        return Room.active_rooms.all()

    def dispatch(self, request, *args, **kwargs):
        return super(RoomDetail, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super(RoomDetail, self).get_context_data(**kwargs)
        room = self.get_object()
        room_data = RoomContext.load(room)
        data.update(room_data)
        player_id = self.request.session.get('player_id')
        if player_id:
            player = get_object_or_404(Player, pk=player_id)
            player_room_data = PlayerRoomContext.load(player, room)
            data.update(player_room_data)
        return data


class JoinRoom(generic.RedirectView, generic.detail.SingleObjectMixin):
    model = Room
    pattern_name = 'room_detail'
    slug_field = 'code'

    def get_redirect_url(self, *args, **kwargs):
        player_id = self.request.session.get('player_id')
        if not player_id:
            raise Exception('Player must be logged in.')
        player = get_object_or_404(Player, pk=player_id)
        room = get_object_or_404(Room, code=kwargs['slug'])
        interfaces.Player2RoomInterface(player, room).join()
        return super().get_redirect_url(*args, **kwargs)


class CreatePlayerAndJoinRoom(AssignPlayerView, generic.CreateView):
    model = Player
    fields = ['name']

    def __init__(self):
        super(CreatePlayerAndJoinRoom, self).__init__()
        self.code = None

    def dispatch(self, request, *args, **kwargs):
        self.code = kwargs['slug']
        player_id = self.request.session.get('player_id')

        if player_id:
            return HttpResponseRedirect(reverse('room_detail', kwargs))
        return super(CreatePlayerAndJoinRoom, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        if type(self.object) is Player:
            player = self.object
            self.assign_player(player)
            return reverse('join_room', kwargs={'slug': self.code})
        return reverse('room_detail', kwargs={'slug': self.code})


class StartGame(generic.RedirectView, generic.detail.SingleObjectMixin):
    model = Room
    pattern_name = 'room_detail'
    slug_field = 'code'

    def get_redirect_url(self, *args, **kwargs):
        room = get_object_or_404(Room, code=kwargs['slug'])
        room_interface = interfaces.RoomGamesInterface(room)
        room_interface.setup()
        game = room_interface.get_current_game()
        game_interface = interfaces.GameRoundsInterface(game)
        game_interface.setup()
        return super().get_redirect_url(*args, **kwargs)


class GameNextRound(generic.RedirectView, generic.detail.SingleObjectMixin):
    model = Room
    pattern_name = 'room_detail'
    slug_field = 'code'

    def get_redirect_url(self, *args, **kwargs):
        game = get_object_or_404(Game, room__code=kwargs['slug'])
        interfaces.GameRoundsInterface(game).next_round()
        return super().get_redirect_url(*args, **kwargs)


class GameCreate(generic.CreateView):
    model = Game
    fields = []

    def form_valid(self, form):
        self.request.session.save()
        form.instance.session_id = self.request.session.session_key
        response = super(GameCreate, self).form_valid(form)
        interfaces.GameInterface(self.object).setup()
        return response

    def get_success_url(self):
        return reverse('game_detail', kwargs={'pk': self.object.pk})


class GameList(generic.ListView):
    context_object_name = 'latest_games'

    def get_queryset(self):
        return Game.objects.order_by('-created')[:5]


class GameDetail(generic.DetailView):
    model = Game


class GenericTeamRoundFormView(generic.FormView):
    class Meta:
        abstract = True

    def __init__(self):
        super(GenericTeamRoundFormView, self).__init__()
        self.room = None
        self.game = None
        self.team = None
        self.opponent_team = None
        self.player = None
        self.current_round = None
        self.current_team_round = None
        self.current_opponent_team_round = None

    def dispatch(self, request, *args, **kwargs):
        room_code = kwargs['slug']
        self.room = get_object_or_404(Room, code=room_code)
        self.game = self.room.current_game
        self.current_round = self.game.current_round
        player_id = self.request.session.get('player_id')
        self.player = get_object_or_404(Player, pk=player_id)
        player_2_room_interface = interfaces.Player2RoomInterface(self.player, self.room)
        self.team = player_2_room_interface.get_team()
        self.opponent_team = player_2_room_interface.get_opponent_team()
        self.current_team_round = self.team.current_team_round
        self.current_opponent_team_round = self.opponent_team.current_team_round
        return super(GenericTeamRoundFormView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super(GenericTeamRoundFormView, self).get_context_data(**kwargs)
        data.update(ContextDataLoader.get_game_data(self.game))
        data.update(ContextDataLoader.get_player_data(self.player, self.game))
        return data

    def get_success_url(self):
        return reverse('room_detail', kwargs={'slug': self.room.code})


class LeaderHintFormSetView(ModelFormSetView, GenericTeamRoundFormView):
    model = LeaderHint
    form_class = HintForm
    factory_kwargs = {
        'extra': 0,
    }

    def get_context_data(self, **kwargs):
        data = super(LeaderHintFormSetView, self).get_context_data(**kwargs)
        data['non_target_words'] = interfaces.PartyRoundInterface(self.game).get_non_target_words()
        return data

    def get_queryset(self):
        return LeaderHint.objects.filter(target_word__team_round=self.current_team_round)

    def formset_valid(self, formset):
        response = super(LeaderHintFormSetView, self).formset_valid(formset)
        interfaces.PartyRoundInterface(self.current_team_round).advance_stage()
        interfaces.RoundInterface(self.current_team_round.round).advance_stage()
        return response


class PlayerGuessFormSetView(ModelFormSetView, GenericTeamRoundFormView):
    model = PlayerGuess
    form_class = GuessForm
    factory_kwargs = {
        'extra': 0,
    }

    def __init__(self):
        super(PlayerGuessFormSetView, self).__init__()
        self.target_words = None

    def dispatch(self, request, *args, **kwargs):
        result = super(PlayerGuessFormSetView, self).dispatch(request, *args, **kwargs)
        self.target_words = TargetWord.objects.filter(team_round=self.current_team_round).all()
        for word in self.target_words:
            PlayerGuess.objects.update_or_create(player=self.player, target_word=word)
        return result

    def get_queryset(self):
        return PlayerGuess.objects.filter(
            player=self.player,
            target_word__team_round=self.current_team_round
        )


class OpponentGuessFormSetView(ModelFormSetView, GenericTeamRoundFormView):
    model = PlayerGuess
    form_class = OpponentGuessForm
    factory_kwargs = {
        'extra': 0,
    }

    def __init__(self):
        super(OpponentGuessFormSetView, self).__init__()
        self.target_words = None

    def dispatch(self, request, *args, **kwargs):
        result = super(OpponentGuessFormSetView, self).dispatch(request, *args, **kwargs)
        self.target_words = TargetWord.objects.filter(team_round=self.current_opponent_team_round).all()
        for word in self.target_words:
            PlayerGuess.objects.update_or_create(player=self.player, target_word=word)
        return result

    def get_queryset(self):
        return PlayerGuess.objects.filter(
            player=self.player,
            target_word__team_round=self.current_opponent_team_round
        )


from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import loader
from django.urls import reverse
from django.views import generic
from extra_views import ModelFormSetView

from core.models import Room, Game, Player, TargetWord, LeaderHint, PlayerGuess
from core import interfaces
from .contexts import RoomContext, Player2RoomContext
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
            player_room_data = Player2RoomContext.load(player, room)
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


class GenericPartyRoundFormView(generic.FormView):
    class Meta:
        abstract = True

    def __init__(self):
        super(GenericPartyRoundFormView, self).__init__()
        self.room = None
        self.player = None
        self.game = None
        self.player_party = None
        self.opponent_party = None
        self.round = None
        self.player_party_round = None
        self.opponent_player_round = None

    def dispatch(self, request, *args, **kwargs):
        room_code = kwargs['slug']
        self.room = get_object_or_404(Room, code=room_code)
        player_id = self.request.session.get('player_id')
        self.player = get_object_or_404(Player, pk=player_id)
        self.game = self.room.current_game
        self.round = self.game.current_round
        player_2_game_interface = interfaces.Player2GameInterface(self.player, self.game)
        self.player_party = player_2_game_interface.get_party()
        self.opponent_party = player_2_game_interface.get_opponent_party()
        self.player_party_round = self.player_party.current_party_round
        self.opponent_player_round = self.opponent_party.current_party_round
        return super(GenericPartyRoundFormView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super(GenericPartyRoundFormView, self).get_context_data(**kwargs)
        data.update(RoomContext.load(self.room))
        data.update(Player2RoomContext.load(self.player, self.room))
        return data

    def get_success_url(self):
        return reverse('room_detail', kwargs={'slug': self.room.code})


class LeaderHintFormSetView(ModelFormSetView, GenericPartyRoundFormView):
    model = LeaderHint
    form_class = HintForm
    factory_kwargs = {
        'extra': 0,
    }

    def get_context_data(self, **kwargs):
        data = super(LeaderHintFormSetView, self).get_context_data(**kwargs)
        data['non_target_words'] = interfaces.PartyRoundInterface(self.player_party_round).get_non_target_words()
        return data

    def get_queryset(self):
        return LeaderHint.objects.filter(target_word__party_round=self.player_party_round)

    def formset_valid(self, formset):
        response = super(LeaderHintFormSetView, self).formset_valid(formset)
        interfaces.PartyRoundInterface(self.player_party_round).advance_stage()
        interfaces.RoundInterface(self.round).advance_stage()
        interfaces.RoundGuessesInterface(self.round).setup()
        return response


class PlayerGuessFormSetView(ModelFormSetView, GenericPartyRoundFormView):
    model = PlayerGuess
    form_class = GuessForm
    factory_kwargs = {
        'extra': 0,
    }

    def __init__(self):
        super(PlayerGuessFormSetView, self).__init__()
        self.target_words = None

    def get_context_data(self, **kwargs):
        data = super(PlayerGuessFormSetView, self).get_context_data(**kwargs)
        data['is_player_party'] = True
        return data

    def dispatch(self, request, *args, **kwargs):
        result = super(PlayerGuessFormSetView, self).dispatch(request, *args, **kwargs)
        interfaces.RoundGuessesInterface(self.round).setup()
        interfaces.Player2PartyRoundGuessesInterface(self.player, self.opponent_player_round).setup()
        return result

    def get_queryset(self):
        return PlayerGuess.objects.filter(
            player=self.player,
            target_word__party_round=self.player_party_round,
        ).order_by('target_word__order')

    def formset_valid(self, formset):
        response = super(PlayerGuessFormSetView, self).formset_valid(formset)
        interface = interfaces.PartyRoundGuessesInterface(self.player_party_round)
        if interface.can_set_party_guess():
            interface.set_party_guess()
        return response


class OpponentGuessFormSetView(ModelFormSetView, GenericPartyRoundFormView):
    model = PlayerGuess
    form_class = OpponentGuessForm
    factory_kwargs = {
        'extra': 0,
    }

    def __init__(self):
        super(OpponentGuessFormSetView, self).__init__()
        self.target_words = None

    def get_context_data(self, **kwargs):
        data = super(OpponentGuessFormSetView, self).get_context_data(**kwargs)
        data['is_player_party'] = False
        return data

    def dispatch(self, request, *args, **kwargs):
        result = super(OpponentGuessFormSetView, self).dispatch(request, *args, **kwargs)
        interfaces.RoundGuessesInterface(self.round).setup()
        interfaces.Player2PartyRoundGuessesInterface(self.player, self.opponent_player_round).setup()
        return result

    def get_queryset(self):
        return PlayerGuess.objects.filter(
            player=self.player,
            target_word__party_round=self.opponent_player_round
        ).order_by('target_word__order')

    def formset_valid(self, formset):
        response = super(OpponentGuessFormSetView, self).formset_valid(formset)

        interface = interfaces.PartyRoundGuessesInterface(self.opponent_player_round)
        if interface.can_set_party_guess():
            interface.set_party_guess()
        return response

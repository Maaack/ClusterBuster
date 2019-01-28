from django.urls import reverse
from django.views import generic
from django.http import HttpResponse
from django.template import loader

from room.models import Room

from .contexts import PlayerContext, GroupContext, Player2RoomContext, Player2GroupContext
from .mixins import CheckPlayerView


def index_view(request):
    template = loader.get_template('room/index.html')
    return HttpResponse(template.render({}, request))


class RoomCreate(generic.CreateView):
    model = Room
    fields = []

    def form_valid(self, form):
        self.request.session.save()
        form.instance.session_id = self.request.session.session_key
        response = super(RoomCreate, self).form_valid(form)
        return response

    def get_success_url(self):
        return reverse('room_detail', kwargs={'slug': self.object.code})


class RoomList(generic.ListView):
    context_object_name = 'active_rooms'

    def get_queryset(self):
        return Room.active_rooms.all()


class RoomDetail(generic.DetailView, CheckPlayerView):
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
        current_player = self.get_current_player()
        if current_player:
            player_data = PlayerContext.load(current_player)
            data.update(player_data)
            player_room_data = Player2RoomContext.load(current_player, room)
            data.update(player_room_data)
        players = room.players.all()
        players_data = list()
        for player in players:
            player_data = PlayerContext.load(player)
            player_room_data = Player2RoomContext.load(player, room)
            player_data.update(player_room_data)
            player_data['is_player'] = player == current_player
            players_data.append(player_data)
        data['players'] = players_data
        groups = room.groups.all()
        groups_data = list()
        for group in groups:
            group_data = GroupContext.load(group)
            if current_player:
                player_group_data = Player2GroupContext.load(current_player, group)
                group_data.update(player_group_data)
            groups_data.append(group_data)
        data['groups'] = groups_data

        return data


class JoinRoom(generic.RedirectView, generic.detail.SingleObjectMixin, CheckPlayerView):
    model = Room
    pattern_name = 'room_detail'
    slug_field = 'code'

    def get_redirect_url(self, *args, **kwargs):
        player = self.get_current_player()
        if not player:
            raise Exception('Player must be logged in.')
        room = self.get_object()
        room.join(player)
        return super().get_redirect_url(*args, **kwargs)

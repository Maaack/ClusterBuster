from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import loader
from django.urls import reverse
from django.views import generic
from extra_views import ModelFormSetView

from core import interfaces
from room.models import Person, Group, Room
from .contexts import RoomContext, Person2RoomContext
from .mixins import CheckPersonView, AssignPersonView


class PersonCreate(AssignPersonView, generic.CreateView):
    model = Person
    fields = ['name']

    def dispatch(self, request, *args, **kwargs):
        person_id = self.request.session.get('person_id')

        if person_id:
            return HttpResponseRedirect(reverse('person_detail', kwargs={'pk':person_id}))
        return super(PersonCreate, self).dispatch(request, *args, **kwargs)


class PersonUpdate(AssignPersonView, CheckPersonView, generic.UpdateView):
    model = Person
    fields = ['name']

    def dispatch(self, request, *args, **kwargs):
        player = self.get_object()

        if not self.is_current_person(player):
            return HttpResponseRedirect(reverse('player_detail', kwargs=kwargs))
        return super(PersonUpdate, self).dispatch(request, *args, **kwargs)


class PersonDetail(generic.DetailView, CheckPersonView):
    model = Person

    def get_context_data(self, **kwargs):
        data = super(PersonDetail, self).get_context_data(**kwargs)
        data['current_person'] = self.is_current_person(self.object)
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
        person_id = self.request.session.get('person_id')
        if person_id:
            person = get_object_or_404(Person, pk=person_id)
            person_room_date = Person2RoomContext.load(person, room)
            data.update(person_room_date)
        return data


class JoinRoom(generic.RedirectView, generic.detail.SingleObjectMixin):
    model = Room
    pattern_name = 'room_detail'
    slug_field = 'code'

    def get_redirect_url(self, *args, **kwargs):
        person_id = self.request.session.get('person_id')
        if not person_id:
            raise Exception('Person must be logged in.')
        person = get_object_or_404(Person, pk=person_id)
        room = get_object_or_404(Room, code=kwargs['slug'])
        room.join(person)
        return super().get_redirect_url(*args, **kwargs)


class CreatePersonAndJoinRoom(AssignPersonView, generic.CreateView):
    model = Person
    fields = ['name']

    def __init__(self):
        super(CreatePersonAndJoinRoom, self).__init__()
        self.code = None

    def dispatch(self, request, *args, **kwargs):
        self.code = kwargs['slug']
        player_id = self.request.session.get('player_id')

        if player_id:
            return HttpResponseRedirect(reverse('room_detail', kwargs))
        return super(CreatePersonAndJoinRoom, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        if type(self.object) is Person:
            player = self.object
            self.assign_player(player)
            return reverse('join_room', kwargs={'slug': self.code})
        return reverse('room_detail', kwargs={'slug': self.code})

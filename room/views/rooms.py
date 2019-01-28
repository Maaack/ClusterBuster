from django.urls import reverse
from django.views import generic
from django.http import HttpResponse
from django.template import loader

from room.models import Room

from .contexts import PersonContext, GroupContext, Person2RoomContext, Person2GroupContext
from .mixins import CheckPersonView


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


class RoomDetail(generic.DetailView, CheckPersonView):
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
        current_person = self.get_current_person()
        if current_person:
            person_data = PersonContext.load(current_person)
            data.update(person_data)
            person_room_data = Person2RoomContext.load(current_person, room)
            data.update(person_room_data)
        people = room.people.all()
        people_data = list()
        for person in people:
            person_data = PersonContext.load(person)
            person_room_data = Person2RoomContext.load(person, room)
            person_data.update(person_room_data)
            person_data['is_person'] = person == current_person
            people_data.append(person_data)
        data['people'] = people_data
        groups = room.groups.all()
        groups_data = list()
        for group in groups:
            group_data = GroupContext.load(group)
            if current_person:
                person_group_data = Person2GroupContext.load(current_person, group)
                group_data.update(person_group_data)
            groups_data.append(group_data)
        data['groups'] = groups_data

        return data


class JoinRoom(generic.RedirectView, generic.detail.SingleObjectMixin, CheckPersonView):
    model = Room
    pattern_name = 'room_detail'
    slug_field = 'code'

    def get_redirect_url(self, *args, **kwargs):
        person = self.get_current_person()
        if not person:
            raise Exception('Person must be logged in.')
        room = self.get_object()
        room.join(person)
        return super().get_redirect_url(*args, **kwargs)

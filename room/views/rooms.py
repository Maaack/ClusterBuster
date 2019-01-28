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
        person = self.get_current_person()
        if person:
            person_data = PersonContext.load(person)
            data.update(person_data)
            person_room_data = Person2RoomContext.load(person, room)
            data.update(person_room_data)
        groups = room.groups.all()
        groups_data = list()
        for count, group in enumerate(groups):
            group_data = GroupContext.load(group)
            if person:
                person_group_data = Person2GroupContext.load(person, group)
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

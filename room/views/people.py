from django.http import HttpResponseRedirect

from django.urls import reverse
from django.views import generic

from room.models import Person
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
        person = self.get_object()

        if not self.is_current_person(person):
            return HttpResponseRedirect(reverse('player_detail', kwargs=kwargs))
        return super(PersonUpdate, self).dispatch(request, *args, **kwargs)


class PersonDetail(generic.DetailView, CheckPersonView):
    model = Person

    def get_context_data(self, **kwargs):
        data = super(PersonDetail, self).get_context_data(**kwargs)
        data['current_person'] = self.is_current_person(self.object)
        return data


class CreatePersonAndJoinRoom(AssignPersonView, CheckPersonView, generic.CreateView):
    model = Person
    fields = ['name']

    def __init__(self):
        super(CreatePersonAndJoinRoom, self).__init__()
        self.code = None

    def dispatch(self, request, *args, **kwargs):
        self.code = kwargs['slug']
        person = self.get_current_person()

        if person is not None:
            return HttpResponseRedirect(reverse('room_detail', kwargs))
        return super(CreatePersonAndJoinRoom, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        if type(self.object) is Person:
            person = self.object
            self.assign_person(person)
            return reverse('join_room', kwargs={'slug': self.code})
        return reverse('room_detail', kwargs={'slug': self.code})

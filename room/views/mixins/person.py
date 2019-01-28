from django.views import generic, View
from django.urls import reverse
from room.models import Person


class CheckPersonView(View):
    class Meta:
        abstract = True

    model = Person

    def is_current_person(self, player):
        return self.get_current_person() == player

    def get_current_person(self):
        player_id = self.request.session.get('player_id')
        if player_id:
            try:
                return Person.objects.get(pk=player_id)
            except Person.DoesNotExist:
                return None


class AssignPersonView(generic.edit.FormMixin, View):
    class Meta:
        abstract = True

    def assign_player(self, person):
        if type(person) is Person:
            self.request.session['person_id'] = person.pk
            self.request.session['person_name'] = person.name

    def form_valid(self, form):
        self.request.session.save()
        form.instance.session_id = self.request.session.session_key
        return super(AssignPersonView, self).form_valid(form)

    def get_success_url(self):
        if type(self.object) is Person:
            player = self.object
            self.assign_player(player)
            return reverse('person_detail', kwargs={'pk': self.object.pk})
        return reverse('person_list')



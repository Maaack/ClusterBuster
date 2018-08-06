from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.views import generic
from django.urls import reverse
from .models import Game, Player


# Create your views here.
def index(request):
    template = loader.get_template('core/index.html')
    return HttpResponse(template.render({}, request))


class GameListView(generic.ListView):
    context_object_name = 'latest_game_list'

    def get_queryset(self):
        return Game.objects.order_by('-created')[:5]


class GameDetailView(generic.DetailView):
    model = Game


class PlayerCreateView(generic.CreateView):
    model = Player
    fields = ['name']

    def form_valid(self, form):
        self.request.session.save()
        form.instance.session_id = self.request.session.session_key
        return super(PlayerCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('player_detail', kwargs={'pk': self.object.pk})


class PlayerUpdateView(generic.UpdateView):
    model = Player
    fields = ['name']

    def form_valid(self, form):
        self.request.session.save()
        form.instance.session_id = self.request.session.session_key
        return super(PlayerUpdateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('player_detail', kwargs={'pk': self.object.pk})


class PlayerDetailView(generic.DetailView):
    model = Player


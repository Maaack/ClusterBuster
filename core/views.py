from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.views import generic
from django.urls import reverse
from django.core.exceptions import MultipleObjectsReturned

from .models import Game, Player


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


class GameDetail(generic.DetailView):
    model = Game


def player_join_game(request, pk):
    if pk and request.session.session_key:
        game = get_object_or_404(Game, pk=pk)
        try:
            player = get_object_or_404(Player, session_id=request.session.session_key)
        except MultipleObjectsReturned:
            player = Player.objects.filter(session_id=request.session.session_key).first()
        game.join(player)

    return HttpResponseRedirect(reverse('game_detail', kwargs={'pk': pk}))


def game_next_round(request, pk):
    if pk:
        game = get_object_or_404(Game, pk=pk)
        game.next_round()

    return HttpResponseRedirect(reverse('game_detail', kwargs={'pk': pk}))


class PlayerCreate(generic.CreateView):
    model = Player
    fields = ['name']

    def form_valid(self, form):
        self.request.session.save()
        form.instance.session_id = self.request.session.session_key
        return super(PlayerCreate, self).form_valid(form)

    def get_success_url(self):
        return reverse('player_detail', kwargs={'pk': self.object.pk})


class PlayerUpdate(generic.UpdateView):
    model = Player
    fields = ['name']

    def form_valid(self, form):
        self.request.session.save()
        form.instance.session_id = self.request.session.session_key
        return super(PlayerUpdate, self).form_valid(form)

    def get_success_url(self):
        return reverse('player_detail', kwargs={'pk': self.object.pk})


class PlayerDetail(generic.DetailView):
    model = Player


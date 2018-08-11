from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.views import generic
from django.urls import reverse
from django.core.exceptions import MultipleObjectsReturned

from .models import Game, Player


class CheckPlayerViewMixin(generic.detail.SingleObjectMixin, generic.View):
    class Meta:
        abstract = True

    def is_current_player(self):
        player = self.get_object()
        return self.request.session['player_id'] == player.pk


class AssignPlayerViewMixin(generic.detail.SingleObjectMixin, generic.View):
    class Meta:
        abstract = True

    def assign_player(self):
        player = self.get_object()
        if player:
            self.request.session['player_id'] = player.pk
            self.request.session['player_name'] = player.name
            return True
        return False


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


class PlayerCreate(generic.CreateView, AssignPlayerViewMixin):
    model = Player
    fields = ['name']

    def dispatch(self, request, *args, **kwargs):
        if request.session['player_id'] is not None:
            return HttpResponseRedirect(reverse('player_detail', kwargs={'pk':request.session['player_id']}))
        return super(PlayerCreate, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.request.session.save()
        form.instance.session_id = self.request.session.session_key
        return super(PlayerCreate, self).form_valid(form)

    def get_success_url(self):
        self.assign_player()
        return reverse('player_detail', kwargs={'pk': self.object.pk})


class PlayerUpdate(generic.UpdateView, AssignPlayerViewMixin, CheckPlayerViewMixin):
    model = Player
    fields = ['name']

    def dispatch(self, request, *args, **kwargs):
        if not self.is_current_player():
            return HttpResponseRedirect(reverse('player_detail', kwargs=kwargs))
        return super(PlayerUpdate, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.request.session.save()
        form.instance.session_id = self.request.session.session_key
        return super(PlayerUpdate, self).form_valid(form)

    def get_success_url(self):
        self.assign_player()
        return reverse('player_detail', kwargs={'pk': self.object.pk})


class PlayerDetail(generic.DetailView, CheckPlayerViewMixin):
    model = Player

    def get_context_data(self, **kwargs):
        data = super(PlayerDetail, self).get_context_data(**kwargs)
        data['current_player'] = self.is_current_player()
        return data


from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.views import generic
from .models import Game


# Create your views here.
def index(request):
    template = loader.get_template('core/index.html')
    return HttpResponse(template.render({}, request))


class GameListView(generic.ListView):
    context_object_name = 'latest_game_list'

    def get_queryset(self):
        return Game.objects.order_by('-created')[:5]

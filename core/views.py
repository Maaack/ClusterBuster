from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from .models import Game


# Create your views here.
def index(request):
    template = loader.get_template('core/index.html')
    return HttpResponse(template.render({}, request))


def games_list(request):
    latest_games_list = Game.objects.order_by('-created')[:5]
    template = loader.get_template('core/games.html')
    context = {
        'latest_games_list': latest_games_list,
    }
    return HttpResponse(template.render(context, request))
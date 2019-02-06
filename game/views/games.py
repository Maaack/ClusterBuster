from django.shortcuts import get_object_or_404
from django.views import generic

from rooms.models import Room
from game.models import Game


class StartGame(generic.RedirectView, generic.detail.SingleObjectMixin):
    model = Room
    pattern_name = 'room_detail'
    slug_field = 'code'

    def get_redirect_url(self, *args, **kwargs):
        room = get_object_or_404(Room, code=kwargs['slug'])
        game = Game()
        game.setup_from_room(room)
        return super().get_redirect_url(*args, **kwargs)
from django.views import generic, View
from django.urls import reverse
from rooms.models import Player


class CheckPlayerView(View):
    class Meta:
        abstract = True

    model = Player

    def is_current_player(self, player):
        return self.get_current_player() == player

    def get_current_player(self):
        player_id = self.request.session.get('player_id')
        if player_id:
            try:
                return Player.objects.get(pk=player_id)
            except Player.DoesNotExist:
                return None
        return None


class AssignPlayerView(generic.edit.FormMixin, View):
    class Meta:
        abstract = True

    def assign_player(self, player):
        if type(player) is Player:
            self.request.session['player_id'] = player.pk
            self.request.session['player_name'] = player.name

    def form_valid(self, form):
        self.request.session.save()
        form.instance.session_id = self.request.session.session_key
        return super(AssignPlayerView, self).form_valid(form)

    def get_success_url(self):
        if type(self.object) is Player:
            player = self.object
            self.assign_player(player)
            return reverse('player_detail', kwargs={'pk': self.object.pk})
        return reverse('player_list')



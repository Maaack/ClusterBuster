from django.views import generic, View
from django.urls import reverse
from rooms.models import Player


class CheckPlayerView(View):
    class Meta:
        abstract = True

    model = Player

    def save_player_to_session(self, player):
        if isinstance(player, Player):
            self.request.session['player_id'] = player.pk
            self.request.session['player_name'] = player.name

    def is_current_player(self, player):
        return self.get_current_player() == player

    def get_current_player(self):
        player_id = self.request.session.get('player_id')
        if player_id:
            try:
                return Player.objects.get(pk=player_id)
            except Player.DoesNotExist:
                return None
        else:
            if self.request.session.session_key is None:
                self.request.session.save()
            session_key = self.request.session.session_key
            try:
                player = Player.objects.get(session_id=session_key)
                self.save_player_to_session(player)
                return player
            except Player.DoesNotExist:
                return None


class AssignPlayerView(generic.edit.FormMixin, CheckPlayerView):
    class Meta:
        abstract = True

    def form_valid(self, form):
        self.request.session.save()
        form.instance.session_id = self.request.session.session_key
        return super(AssignPlayerView, self).form_valid(form)

    def get_success_url(self):
        if isinstance(self.object, Player):
            player = self.object
            self.save_player_to_session(player)
            return reverse('player_detail', kwargs={'pk': self.object.pk})
        return reverse('player_list')



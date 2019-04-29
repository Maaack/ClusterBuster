from django.contrib import admin

from .models import Player, Team, Lobby, Activity, ActivityOption

admin.site.register(Player)
admin.site.register(Team)
admin.site.register(Lobby)
admin.site.register(Activity)
admin.site.register(ActivityOption)

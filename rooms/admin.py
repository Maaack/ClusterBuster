from django.contrib import admin

from .models import Player, Team, Room, Activity

admin.site.register(Player)
admin.site.register(Team)
admin.site.register(Room)
admin.site.register(Activity)

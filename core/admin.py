from django.contrib import admin

# Register your models here.

from .models import Game, GameRoom, Team, Player, Word

admin.site.register(Game)
admin.site.register(GameRoom)
admin.site.register(Team)
admin.site.register(Player)
admin.site.register(Word)
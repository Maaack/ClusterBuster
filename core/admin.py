from django.contrib import admin

# Register your models here.

from .models import Game, GameRoom, Team, Player, Word, TeamWord, Round, TeamRound, TeamRoundWord, TeamRoundWordHint

admin.site.register(Game)
admin.site.register(GameRoom)
admin.site.register(Team)
admin.site.register(Player)
admin.site.register(Word)
admin.site.register(TeamWord)
admin.site.register(Round)
admin.site.register(TeamRound)
admin.site.register(TeamRoundWord)
admin.site.register(TeamRoundWordHint)

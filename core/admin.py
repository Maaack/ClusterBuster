from django.contrib import admin

# Register your models here.

from . import models


class PlayerGuessAdmin(admin.ModelAdmin):
    list_display = ('player', 'target_word', 'guess')


class PartyGuessAdmin(admin.ModelAdmin):
    list_display = ('party', 'target_word', 'guess')


admin.site.register(models.Word)
admin.site.register(models.Player)
admin.site.register(models.Team)
admin.site.register(models.Room)
admin.site.register(models.Game)
admin.site.register(models.Party)
admin.site.register(models.PartyWord)
admin.site.register(models.Round)
admin.site.register(models.PartyRound)
admin.site.register(models.TargetWord)
admin.site.register(models.LeaderHint)
admin.site.register(models.PlayerGuess, PlayerGuessAdmin)
admin.site.register(models.PartyGuess, PartyGuessAdmin)

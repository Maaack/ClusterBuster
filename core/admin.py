from django.contrib import admin

# Register your models here.

from . import models

admin.site.register(models.Word)
admin.site.register(models.State)
admin.site.register(models.StateMachine)
admin.site.register(models.ClusterBuster)

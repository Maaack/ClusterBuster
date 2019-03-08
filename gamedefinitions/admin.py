from django.contrib import admin

from .models import *

admin.site.register(Rule)
admin.site.register(State)
admin.site.register(GameDefinition)

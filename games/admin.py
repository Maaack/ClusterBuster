from django.contrib import admin

from .models import *

admin.site.register(Condition)
admin.site.register(ConditionalTransition)
admin.site.register(ParameterKey)
admin.site.register(ParameterValue)
admin.site.register(Parameter)
admin.site.register(Transition)
admin.site.register(StateMachine)
admin.site.register(Game)

from django.contrib import admin

from .models import *

admin.site.register(Condition)
admin.site.register(ConditionGroup)
admin.site.register(ConditionalTransition)
admin.site.register(Parameter)
admin.site.register(Transition)
admin.site.register(Trigger)
admin.site.register(StateMachine)
admin.site.register(Game)
admin.site.register(MixedValue)

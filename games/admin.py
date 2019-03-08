from django.contrib import admin

from .models import *

admin.site.register(BooleanCondition)
admin.site.register(ParameterComparisonCondition)
admin.site.register(Parameter)
admin.site.register(Transition)
admin.site.register(StateMachine)
admin.site.register(Game)

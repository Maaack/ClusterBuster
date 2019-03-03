from django.contrib import admin

from .models import *

admin.site.register(BooleanCondition)
admin.site.register(FixedIntegerCondition)
admin.site.register(VariableIntegerCondition)
admin.site.register(Parameter)
admin.site.register(Transition)
admin.site.register(State)
admin.site.register(StateMachine)
admin.site.register(Game)

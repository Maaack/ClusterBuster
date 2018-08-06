from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('games', views.games_list, name='games'),

]
from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('games', views.GameList.as_view(), name='games'),
    path('game/<int:pk>', views.GameDetail.as_view(), name='game_detail'),
    path('player/create', views.PlayerCreate.as_view(), name='player_create'),
    path('player/<int:pk>', views.PlayerDetail.as_view(), name='player_detail'),
    path('player/<int:pk>/update', views.PlayerUpdate.as_view(), name='player_update'),

]
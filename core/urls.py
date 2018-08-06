from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('games', views.GameList.as_view(), name='games'),
    path('game/start', views.GameCreate.as_view(), name='game_create'),
    path('game/<int:pk>', views.GameDetail.as_view(), name='game_detail'),
    path('game/<int:pk>/join', views.player_join_game, name='player_join_game'),
    path('player/create', views.PlayerCreate.as_view(), name='player_create'),
    path('player/<int:pk>', views.PlayerDetail.as_view(), name='player_detail'),
    path('player/<int:pk>/update', views.PlayerUpdate.as_view(), name='player_update'),

]
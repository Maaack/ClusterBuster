from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('games', views.GameList.as_view(), name='game_list'),
    path('game/start', views.GameCreate.as_view(), name='game_create'),
    path('game/<int:pk>', views.GameDetail.as_view(), name='game_detail'),
    path('rooms/', views.GameRoomList.as_view(), name='gameroom_list'),
    path('room/<slug:slug>', views.GameRoomDetail.as_view(), name='gameroom_detail'),
    path('room/<slug:slug>/join', views.PlayerJoinGame.as_view(), name='player_join_game'),
    path('room/<slug:slug>/next_round', views.GameNextRound.as_view(), name='game_next_round'),
    path('room/<slug:slug>/hints', views.TeamRoundWordFormSetView.as_view(), name='round_hints'),
    path('room/<slug:slug>/guesses', views.PlayerGuessFormSetView.as_view(), name='round_guesses'),
    path('player/create', views.PlayerCreate.as_view(), name='player_create'),
    path('player/<int:pk>', views.PlayerDetail.as_view(), name='player_detail'),
    path('player/<int:pk>/update', views.PlayerUpdate.as_view(), name='player_update'),

]
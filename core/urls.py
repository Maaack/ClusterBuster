from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('new_player/', views.PlayerCreate.as_view(), name='player_create'),
    path('players/<int:pk>', views.PlayerDetail.as_view(), name='player_detail'),
    path('players/<int:pk>/update', views.PlayerUpdate.as_view(), name='player_update'),
    path('new_room/', views.RoomCreate.as_view(), name='room_create'),
    path('rooms/', views.RoomList.as_view(), name='room_list'),
    path('rooms/<slug:slug>', views.RoomDetail.as_view(), name='room_detail'),
    path('rooms/<slug:slug>/join', views.PlayerJoinRoom.as_view(), name='player_join_room'),
    path('rooms/<slug:slug>/start_game', views.RoomStartGame.as_view(), name='room_start_game'),
    path('games/<int:pk>', views.GameList.as_view(), name='game_list'),
    path('game/start', views.GameCreate.as_view(), name='game_create'),
    path('game_room/<slug:slug>/next_round', views.GameNextRound.as_view(), name='game_next_round'),
    path('game_room/<slug:slug>/hints', views.LeaderHintFormSetView.as_view(), name='round_hints'),
    path('game_room/<slug:slug>/guesses', views.PlayerGuessFormSetView.as_view(), name='round_guesses'),
    path('game_room/<slug:slug>/opponent_guesses', views.OpponentGuessFormSetView.as_view(), name='round_opponent_guesses'),

]
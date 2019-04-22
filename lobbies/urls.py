from django.urls import path

from .views import (
    index_view, PlayerCreate, PlayerDetail, PlayerUpdate, LobbyCreate, LobbyList, LobbyDetail, JoinLobby,
    CreatePlayerAndJoinLobby
)

urlpatterns = [
    path('', index_view, name='index'),
    path('new_player/', PlayerCreate.as_view(), name='player_create'),
    path('players/<int:pk>/', PlayerDetail.as_view(), name='player_detail'),
    path('players/<int:pk>/update/', PlayerUpdate.as_view(), name='player_update'),
    path('new_lobby/', LobbyCreate.as_view(), name='lobby_create'),
    path('lobbies/', LobbyList.as_view(), name='lobby_list'),
    path('lobbies/<slug:slug>/', LobbyDetail.as_view(), name='lobby_detail'),
    path('lobbies/<slug:slug>/join/', JoinLobby.as_view(), name='join_lobby'),
    path('lobbies/<slug:slug>/new_player/', CreatePlayerAndJoinLobby.as_view(), name='player_create_and_join_lobby'),
]

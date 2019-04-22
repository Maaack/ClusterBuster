from django.urls import path

from .views.lobbies import index_view, LobbyCreate, LobbyDetail, LobbyList, JoinLobby
from .views.players import PlayerCreate, PlayerDetail, PlayerUpdate
from .views.teams import TeamCreate, TeamDetail, TeamUpdate

urlpatterns = [
    path('', index_view, name='index'),
    path('new_player/', PlayerCreate.as_view(), name='player_create'),
    path('players/<int:pk>/', PlayerDetail.as_view(), name='player_detail'),
    path('players/<int:pk>/update/', PlayerUpdate.as_view(), name='player_update'),
    path('new_team/', TeamCreate.as_view(), name='team_create'),
    path('teams/<int:pk>/', TeamDetail.as_view(), name='team_detail'),
    path('teams/<int:pk>/update/', TeamUpdate.as_view(), name='team_update'),
    path('new_lobby/', LobbyCreate.as_view(), name='lobby_create'),
    path('lobbies/', LobbyList.as_view(), name='lobby_list'),
    path('lobbies/<slug:slug>/', LobbyDetail.as_view(), name='lobby_detail'),
    path('lobbies/<slug:slug>/join/', JoinLobby.as_view(), name='join_lobby'),
]

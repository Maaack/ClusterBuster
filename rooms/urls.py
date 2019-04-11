from django.urls import path

from .views import (
    index_view, PlayerCreate, PlayerDetail, PlayerUpdate, RoomCreate, RoomList, RoomDetail, CreatePlayerAndJoinRoom,
    JoinRoom
)

urlpatterns = [
    path('', index_view, name='index'),
    path('new_player/', PlayerCreate.as_view(), name='player_create'),
    path('players/<int:pk>/', PlayerDetail.as_view(), name='player_detail'),
    path('players/<int:pk>/update', PlayerUpdate.as_view(), name='player_update'),
    path('new_room/', RoomCreate.as_view(), name='room_create'),
    path('rooms/', RoomList.as_view(), name='room_list'),
    path('rooms/<slug:slug>/', RoomDetail.as_view(), name='room_detail'),
    path('rooms/<slug:slug>/new_player', CreatePlayerAndJoinRoom.as_view(), name='player_create_and_join_room'),
    path('rooms/<slug:slug>/join', JoinRoom.as_view(), name='join_room'),
]

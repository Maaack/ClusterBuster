from django.urls import path

from .views import (
    PersonCreate, PersonDetail, PersonUpdate, RoomCreate, RoomList, RoomDetail, CreatePersonAndJoinRoom, JoinRoom
)

urlpatterns = [
    path('new_player/', PersonCreate.as_view(), name='person_create'),
    path('players/<int:pk>', PersonDetail.as_view(), name='person_detail'),
    path('players/<int:pk>/update', PersonUpdate.as_view(), name='person_update'),
    path('new_room/', RoomCreate.as_view(), name='room_create'),
    path('rooms/', RoomList.as_view(), name='room_list'),
    path('rooms/<slug:slug>', RoomDetail.as_view(), name='room_detail'),
    path('rooms/<slug:slug>/new_player', CreatePersonAndJoinRoom.as_view(), name='person_create_and_join_room'),
    path('rooms/<slug:slug>/join', JoinRoom.as_view(), name='join_room'),
]

from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('games', views.GameListView.as_view(), name='games'),
    path('game/<int:pk>', views.GameDetailView.as_view(), name='game_detail'),
    path('player/create', views.PlayerCreateView.as_view(), name='player_create'),
    path('player/<int:pk>', views.PlayerDetailView.as_view(), name='player_detail'),
    path('player/<int:pk>/update', views.PlayerUpdateView.as_view(), name='player_update'),

]
from django.urls import path

from . import views

urlpatterns = [
    path('rooms/<slug:slug>/start_game', views.StartGame.as_view(), name='start_game'),
    path('games/<slug:slug>/', views.GameDetail.as_view(), name='game_detail'),
    path('games/<slug:slug>/update_game', views.UpdateGame.as_view(), name='update_game'),
    path('games/<slug:slug>/leader_hints', views.LeaderHintsFormView.as_view(), name='leader_hints'),
    path('games/<slug:slug>/player_guesses', views.PlayerGuessesFormView.as_view(), name='player_guesses'),

]
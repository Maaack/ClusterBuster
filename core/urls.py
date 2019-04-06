from django.urls import path

from . import views

urlpatterns = [
    path('games/<slug:slug>', views.GameDetail.as_view(), name='game_detail'),
    path('rooms/<slug:slug>/start_game', views.StartGame.as_view(), name='start_game'),
    path('rooms/<slug:slug>/update_game', views.UpdateGame.as_view(), name='update_game'),
    path('rooms/<slug:slug>/leader_hints', views.LeaderHintsFormView.as_view(), name='leader_hints'),
    path('rooms/<slug:slug>/player_guesses', views.PlayerGuessesFormView.as_view(), name='player_guesses'),

]
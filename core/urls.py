from django.urls import path

from . import views

urlpatterns = [
    path('rooms/<slug:slug>/start_game', views.StartGame.as_view(), name='start_game'),
    path('rooms/<slug:slug>/update_game', views.UpdateGame.as_view(), name='update_game'),

]
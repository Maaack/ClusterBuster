from django.urls import path

from . import views

urlpatterns = [
    path('rooms/<slug:slug>/start_game', views.StartGame.as_view(), name='start_game'),

]
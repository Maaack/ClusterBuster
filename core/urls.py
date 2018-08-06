from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('games', views.GameListView.as_view(), name='games'),
    path('game/<int:pk>', views.GameDetailView.as_view(), name='game_detail'),

]
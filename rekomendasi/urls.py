# rekomendasi/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name="login"),
    path('register/', views.register_view, name="register"),
    path('logout/', views.logout_view, name="logout"),
    
    path('home/', views.home, name="home"),
    path('search_tfidf/', views.search_tfidf, name="search_tfidf"),
    path('detail/<str:place_id>/', views.detail_wisata, name="detail_wisata"),
    path("toggle-favorite/<uuid:place_id>/", views.toggle_favorite, name="toggle_favorite"),
    path('favorit/', views.list_favorites, name='list_favorites'),
]




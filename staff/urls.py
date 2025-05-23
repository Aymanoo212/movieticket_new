from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    path('', views.StaffDashboardView.as_view(), name='dashboard'),
    path('film/add/', views.FilmCreateView.as_view(), name='film_add'),
    path('film/<int:pk>/edit/', views.FilmUpdateView.as_view(), name='film_edit'),
    path('film/<int:pk>/delete/', views.FilmDeleteView.as_view(), name='film_delete'),
    path('show/add/', views.ShowCreateView.as_view(), name='show_add'),
    path('show/<int:pk>/edit/', views.ShowUpdateView.as_view(), name='show_edit'),
    path('show/<int:pk>/delete/', views.ShowDeleteView.as_view(), name='show_delete'),
    path('banner/add/', views.BannerCreateView.as_view(), name='banner_add'),
    path('banner/<int:pk>/edit/', views.BannerUpdateView.as_view(), name='banner_edit'),
    path('banner/<int:pk>/delete/', views.BannerDeleteView.as_view(), name='banner_delete'),
    path('salle/add/', views.SalleCreateView.as_view(), name='salle_add'),
    path('salle/<int:pk>/edit/', views.SalleUpdateView.as_view(), name='salle_edit'),
    path('salle/<int:pk>/delete/', views.SalleDeleteView.as_view(), name='salle_delete'),
]
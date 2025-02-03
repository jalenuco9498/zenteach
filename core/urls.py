from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.contrib import admin
urlpatterns = [
    # Rutas principales
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('registro/', views.register, name='register'),
    path('perfil/', views.profile, name='profile'),
    path('nueva_reserva/', views.nueva_reserva, name='nueva_reserva'),
    path('guardar_reserva/', views.guardar_reserva, name='guardar_reserva'),
    path('admin/', views.admin,name='admin'),
    # Rutas de reservas
    path('reservar/', views.reservar, name='reservar'),
    path('api/reservar/<int:servicio_id>/', views.crear_reserva_api, name='crear_reserva_api'),
    path('mis-reservas/', views.historial_reservas, name='historial_reservas'),
]
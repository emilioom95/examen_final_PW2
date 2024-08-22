from django.urls import path
from . import views

urlpatterns = [
    path('examen/', views.iniciar_examen, name='iniciar_examen'),
    path('guardar_resultado/', views.guardar_resultado, name='guardar_resultado'),
    path('resultado_examen/', views.resultado_examen, name='resultado_examen'),
    path('crear_usuario/', views.crear_usuario, name='crear_usuario'),
    path('login/', views.login_view, name='login'),
    path('examen/', views.examen_view, name='examen'),
]

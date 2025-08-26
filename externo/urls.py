from django.urls import path
from . import views

urlpatterns = [
    path('', views.consulta_posicao, name='consulta_posicao'),
]

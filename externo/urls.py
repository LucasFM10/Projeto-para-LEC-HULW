from django.urls import path
from . import views

urlpatterns = [
    path(
        'consulta-posicao',
        views.consulta_posicao,
        name='consulta_posicao'
    ),
    path(
        "indicadores-especialidades",
        views.indicadores_especialidades,
        name="indicadores_especialidades"
    ),
]

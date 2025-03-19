from django.urls import path
from .views import get_especialidade

urlpatterns = [
    path("get_especialidade/<int:procedimento_id>/",
         get_especialidade, name="get_especialidade"),
]

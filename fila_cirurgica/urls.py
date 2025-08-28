from django.urls import path

from portal.views import paciente_api_validate
from . import views

app_name = 'fila_cirurgica'

urlpatterns = [
    # URLs para os autocompletes via API
    path('api/procedimento-autocomplete/', views.procedimento_api_autocomplete, name='procedimento_api_autocomplete'),
    path('api/paciente-autocomplete/', views.paciente_api_autocomplete, name='paciente_api_autocomplete'),
    path('api/medico-autocomplete/', views.medico_api_autocomplete, name='medico_api_autocomplete'),
    path('api/especialidade-autocomplete/', views.especialidade_api_autocomplete, name='especialidade_api_autocomplete'),
    path("api/validate/paciente/", paciente_api_validate, name="paciente_api_validate"),
]
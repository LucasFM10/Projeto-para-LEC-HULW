from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group
from unfold.contrib.filters.admin import AutocompleteSelectMultipleFilter

from django.contrib import admin
from .models import Paciente, ListaEsperaCirurgica, ProcedimentoAghu, Especialidade, Medico, EspecialidadeProcedimento
from .forms import PacienteForm

from unfold.admin import ModelAdmin

admin.site.unregister(User)
admin.site.unregister(Group)

@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    pass

@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass

@admin.register(Paciente)
class PacienteAdmin(ModelAdmin):
    list_display = ('nome', 'data_nascimento', 'sexo')  # Campos exibidos na lista de pacientes

    form = PacienteForm
    
    search_fields = ['nome']

    class Media:
        js = (
            "jquery.mask.min.js",
            "custom.js"
        )

@admin.register(ProcedimentoAghu)
class ProcedimentoAdmin(ModelAdmin):
    search_fields = ['codigo', 'nome']

@admin.register(ListaEsperaCirurgica)
class ListaEsperaCirurgicaAdmin(ModelAdmin):
    list_display = ('get_procedimento','paciente__nome', 'get_posicao')

    readonly_fields = ['data_entrada']
    
    autocomplete_fields = ['paciente', 'procedimento']
    
    list_filter_submit = True
    
    list_filter = [
        ("especialidade", AutocompleteSelectMultipleFilter),
    ]
    
    @admin.display(description="Procedimento Realizado")
    def get_procedimento(self, obj):
        return obj.procedimento

@admin.register(Especialidade)
class EspecialidadeAdmin(ModelAdmin):
    list_display = ('cod_especialidade','nome_especialidade')
    
    search_fields = ['nome_especialidade', 'cod_especialidade']

@admin.register(Medico)
class MedicoAdmin(ModelAdmin):
    list_display = ('nome','matricula')
    
    autocomplete_fields = ['especialidades']

@admin.register(EspecialidadeProcedimento)
class EspecialidadeProcedimentoAdmin(ModelAdmin):
    list_display = ('especialidade','procedimento')
    
    autocomplete_fields = ['especialidade', 'procedimento']
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group
from unfold.contrib.filters.admin import TextFilter, FieldTextFilter, RelatedDropdownFilter

from django.contrib import admin
from .models import Paciente, Procedimento, ListaEsperaCirurgica, ProcedimentoAghu, Especialidade, Medico
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

@admin.register(Procedimento)
class ProcedimentoAdmin(ModelAdmin):
    search_fields = ['codigo', 'nome']

@admin.register(ProcedimentoAghu)
class ProcedimentoAdmin(ModelAdmin):
    search_fields = ['codigo', 'nome']

@admin.register(ListaEsperaCirurgica)
class ListaEsperaCirurgicaAdmin(ModelAdmin):
    list_display = ('procedimentos__nome','paciente__nome', 'pontos')

    readonly_fields = ['pontos', 'data_entrada']
    
    autocomplete_fields = ['paciente', 'procedimentos']

    ordering = ('-pontos', )
    
    list_filter_submit = True  # Submit button at the bottom of the filter
    list_filter = [
        ("especialidade", RelatedDropdownFilter),
        ("paciente", RelatedDropdownFilter),
    ]

@admin.register(Especialidade)
class EspecialidadeAdmin(ModelAdmin):
    list_display = ('cod_especialidade','nome_especialidade')

@admin.register(Medico)
class MedicoAdmin(ModelAdmin):
    list_display = ('nome','matricula')
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group
from unfold.contrib.filters.admin import AutocompleteSelectMultipleFilter

from django.contrib import admin
from .models import Paciente, ListaEsperaCirurgica, ProcedimentoAghu, Especialidade, Medico, EspecialidadeProcedimento
from .forms import PacienteForm, ListaEsperaCirurgicaForm

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

    def get_search_results(self, request, queryset, search_term):
        # Filtra apenas os procedimentos que possuem uma especialidade associada
        queryset = queryset.filter(especialidadeprocedimento__isnull=False).distinct()

        return super().get_search_results(request, queryset, search_term)

@admin.register(ListaEsperaCirurgica)
class ListaEsperaCirurgicaAdmin(ModelAdmin):
    list_display = ('get_especialidade', 'get_procedimento', 'get_paciente', 'get_posicao')
    
    form = ListaEsperaCirurgicaForm
    
    autocomplete_fields = ["procedimento", "paciente", "medico"]  # Aplica autocomplete corretamente

    list_filter_submit = True

    list_filter = [
        ("procedimento__especialidadeprocedimento__especialidade", AutocompleteSelectMultipleFilter),
    ]

    def get_especialidade(self, obj):
        """ Retorna a especialidade associada ao procedimento """
        if obj.procedimento:
            especialidade_procedimento = EspecialidadeProcedimento.objects.filter(procedimento=obj.procedimento).first()
            return especialidade_procedimento.especialidade.nome_especialidade if especialidade_procedimento else "Sem Especialidade"
        return "Sem Especialidade"
    
    get_especialidade.short_description = "Especialidade"
    
    @admin.display(description="Procedimento Realizado")
    def get_procedimento(self, obj):
        return obj.procedimento
    
    @admin.display(description="Nome do Paciente")
    def get_paciente(self, obj):
        return obj.paciente
    
    class Media:
        js = (
            "https://code.jquery.com/jquery-3.6.0.min.js",  # Garante o carregamento do jQuery
            "custom1.js",
        )



@admin.register(Especialidade)
class EspecialidadeAdmin(ModelAdmin):
    list_display = ('cod_especialidade','nome_especialidade')
    
    search_fields = ['nome_especialidade', 'cod_especialidade']

@admin.register(Medico)
class MedicoAdmin(ModelAdmin):
    list_display = ('nome','matricula')
    
    autocomplete_fields = ['especialidades']
    search_fields = ['nome']

@admin.register(EspecialidadeProcedimento)
class EspecialidadeProcedimentoAdmin(ModelAdmin):
    list_display = ('especialidade','procedimento')
    
    autocomplete_fields = ['especialidade', 'procedimento']
    
    search_fields = ['especialidade__nome_especialidade', 'procedimento__nome']
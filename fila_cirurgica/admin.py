from django.db.models import Case, When, IntegerField
from django.db.models import Q
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group
from unfold.contrib.filters.admin import AutocompleteSelectMultipleFilter, DropdownFilter
from simple_history.admin import SimpleHistoryAdmin

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
    # Campos exibidos na lista de pacientes
    list_display = ('nome', 'data_nascimento', 'sexo')

    form = PacienteForm

    search_fields = ['nome']

    class Media:
        js = (
            "js/masks/jquery.mask.min.js",
            "js/masks/custom.js"
        )


@admin.register(ProcedimentoAghu)
class ProcedimentoAdmin(ModelAdmin):
    search_fields = ['codigo', 'nome']

    def get_search_results(self, request, queryset, search_term):

        filter_conditions = Q()

        # Aplica filtro para especialidadeprocedimento
        filter_conditions &= Q(especialidadeprocedimento__isnull=False)

        queryset = queryset.filter(filter_conditions).distinct()

        return super().get_search_results(request, queryset, search_term)


@admin.register(ListaEsperaCirurgica)
class ListaEsperaCirurgicaAdmin(SimpleHistoryAdmin, ModelAdmin):
    list_display = ('get_paciente', 'paciente_oncologico', 'urgencia', 'medida_judicial',
                    'get_especialidade', 'get_procedimento', 'get_posicao')

    readonly_fields = ['data_entrada']

    form = ListaEsperaCirurgicaForm

    autocomplete_fields = ["procedimento", "paciente",
                           "medico"]  # Aplica autocomplete corretamente

    list_filter_submit = True

    list_filter = [
        ("procedimento__especialidadeprocedimento__especialidade",
         AutocompleteSelectMultipleFilter),
        ("procedimento",
         AutocompleteSelectMultipleFilter),
        ("medico", AutocompleteSelectMultipleFilter),
    ]

    @admin.display(description="Especialidade")
    def get_especialidade(self, obj):
        """ Retorna a especialidade associada ao procedimento """
        if obj.procedimento:
            especialidade_procedimento = EspecialidadeProcedimento.objects.filter(
                procedimento=obj.procedimento).first()
            return especialidade_procedimento.especialidade.nome_especialidade if especialidade_procedimento else "Sem Especialidade"
        return "Sem Especialidade"

    @admin.display(description="Procedimento Realizado")
    def get_procedimento(self, obj):

        return obj.procedimento

    @admin.display(description="Nome do Paciente")
    def get_paciente(self, obj):
        return obj.paciente

    def history_view(self, request, object_id, extra_context=None):
        print(object_id)
        return super().history_view(request, object_id, extra_context)

    @admin.display(description="Posição na Fila")
    def get_posicao(self, obj):
        queryset = ListaEsperaCirurgica.objects.annotate(
            prioridade=Case(
                When(medida_judicial=True, then=0),
                When(paciente_oncologico=True, then=1),
                When(urgencia=True, then=2),
                default=3,
                output_field=IntegerField()
            )
        ).order_by('prioridade', 'data_entrada').values_list('id', flat=True)

        return list(queryset).index(obj.id) + 1

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            prioridade=Case(
                When(medida_judicial=True, then=0),
                When(paciente_oncologico=True, then=1),
                When(urgencia=True, then=2),
                default=3,
                output_field=IntegerField()
            )
        ).order_by('prioridade', 'data_entrada')


@admin.register(Especialidade)
class EspecialidadeAdmin(ModelAdmin):
    list_display = ('cod_especialidade', 'nome_especialidade')

    search_fields = ['nome_especialidade', 'cod_especialidade']


@admin.register(Medico)
class MedicoAdmin(ModelAdmin):
    list_display = ('nome', 'matricula')

    autocomplete_fields = ['especialidades']
    search_fields = ['nome']


@admin.register(EspecialidadeProcedimento)
class EspecialidadeProcedimentoAdmin(ModelAdmin):
    list_display = ('especialidade', 'procedimento')

    autocomplete_fields = ['especialidade', 'procedimento']

    search_fields = ['especialidade__nome_especialidade', 'procedimento__nome']

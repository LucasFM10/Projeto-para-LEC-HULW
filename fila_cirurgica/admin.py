from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import AutocompleteSelectMultipleFilter
from django.contrib.admin import SimpleListFilter
from django.db.models import Count
from django.template.response import TemplateResponse
from django.urls import path
from django.http import JsonResponse
from .models import (
    Paciente,
    ListaEsperaCirurgica,
    ProcedimentoAghu,
    Especialidade,
    Medico,
    EspecialidadeProcedimento,
    IndicadorEspecialidade,
)
from .forms import PacienteForm, ListaEsperaCirurgicaForm

# Registro de usuário e grupo personalizados
admin.site.unregister(User)
admin.site.unregister(Group)

@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    pass

@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


@admin.register(IndicadorEspecialidade)
class IndicadorEspecialidadeAdmin(admin.ModelAdmin):
    # não exibe os botões de adicionar/editar
    has_add_permission = lambda self, request: False
    has_change_permission = lambda self, request, obj=None: False
    has_delete_permission = lambda self, request, obj=None: False

    change_list_template = 'admin/indicadores_especialidade.html'

    def changelist_view(self, request, extra_context=None):
        # Obtém contagem por especialidade
        qs = (
            ListaEsperaCirurgica.objects
                .values('especialidade__nome_especialidade')
                .annotate(total=Count('id'))
        )
        total_geral = ListaEsperaCirurgica.objects.count() or 1
        # prepara dados para gráfico
        labels = [item['especialidade__nome_especialidade'] for item in qs]
        data = [item['total'] for item in qs]
        percentages = [round(item['total'] / total_geral * 100, 2) for item in qs]

        context = {
            'labels': labels,
            'data': data,
            'percentages': percentages,
        }
        return TemplateResponse(request, self.change_list_template, {**self.admin_site.each_context(request), **context})


@admin.register(Paciente)
class PacienteAdmin(ModelAdmin):
    form = PacienteForm
    list_display = ('nome', 'data_nascimento', 'sexo')
    search_fields = ['nome']

    class Media:
        js = (
            "js/masks/jquery.mask.min.js",
            "js/masks/custom.js",
        )


class DemandaPedagogicaFilter(SimpleListFilter):
    title = 'Demanda Pedagógica'
    parameter_name = 'demanda_pedagogica'

    def lookups(self, request, model_admin):
        return (
            ('com', 'Com demanda'),
            ('sem', 'Sem demanda'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'com':
            return queryset.filter(
                procedimento__especialidadeprocedimento__especialidade__demanda_pedagogica=True
            ).distinct()
        if self.value() == 'sem':
            return queryset.exclude(
                procedimento__especialidadeprocedimento__especialidade__demanda_pedagogica=True
            ).distinct()
        return queryset

@admin.register(ListaEsperaCirurgica)
class ListaEsperaCirurgicaAdmin(SimpleHistoryAdmin, ModelAdmin):
    form = ListaEsperaCirurgicaForm
    readonly_fields = ['data_entrada']
    autocomplete_fields = ['especialidade', 'procedimento', 'paciente', 'medico']

    list_display = (
        'get_posicao',
        'paciente',
        'prioridade',
        'medida_judicial',
        'demanda_pedagogica',
        'especialidade',
        'procedimento',
    )
    list_filter_submit = True
    list_filter = [
        ('especialidade', AutocompleteSelectMultipleFilter),
        ('procedimento', AutocompleteSelectMultipleFilter),
        ('medico', AutocompleteSelectMultipleFilter),
        (DemandaPedagogicaFilter)
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return (
            qs
            .with_prioridade_index()        # já anota demanda_pedagogica_bool se você usou o Exists
            .order_by(
                'prioridade_num',
                'demanda_pedagogica_num',
                'data_entrada'
            )
        )

    @admin.display(description="Demanda Pedagógica", boolean=True)
    def demanda_pedagogica(self, obj):
        # Se você anotou demanda_pedagogica_bool, pode fazer:
        if hasattr(obj, 'demanda_pedagogica_bool'):
            return obj.demanda_pedagogica_bool

    @admin.display(description="Posição na Fila")
    def get_posicao(self, obj):
        return obj.get_posicao()

    @admin.display(description="Especialidade")
    def especialidade(self, obj):
        return obj.especialidade or "Sem Especialidade"

    @admin.display(description="Procedimento Realizado")
    def procedimento(self, obj):
        return obj.procedimento

@admin.register(ProcedimentoAghu)
class ProcedimentoAdmin(ModelAdmin):
    search_fields = ['codigo', 'nome']

    def get_search_results(self, request, queryset, search_term):
        queryset = queryset.filter(especialidadeprocedimento__isnull=False).distinct()
        return super().get_search_results(request, queryset, search_term)


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

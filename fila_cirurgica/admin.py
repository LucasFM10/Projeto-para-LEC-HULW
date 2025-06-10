from django.contrib import admin, messages
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
from django.utils.timezone import now
from datetime import timedelta
from django.db.models.functions import TruncMonth
from django.db.models import Count, Min
from django import forms
from django.shortcuts import redirect, render
from django import forms
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from django.views.generic import FormView
from unfold.views import UnfoldModelAdminViewMixin

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
        # últimos 3 meses
        hoje = now().date()
        inicio_periodo = hoje.replace(day=1) - timedelta(days=60)
        # Obtém contagem por especialidade
        qs = (
            ListaEsperaCirurgica.objects
                .values('especialidade__nome_especialidade')
                .annotate(total=Count('id'))
        )
        # Agrupamento por mês
        qs_mensal = (
            ListaEsperaCirurgica.objects
            .filter(data_entrada__date__gte=inicio_periodo)
            .annotate(mes=TruncMonth('data_entrada'))
            .values('mes')
            .annotate(total=Count('id'))
            .order_by('mes')
        )
        total_geral = ListaEsperaCirurgica.objects.count() or 1
        # prepara dados para gráfico
        labels = [item['especialidade__nome_especialidade'] for item in qs]
        data = [item['total'] for item in qs]
        percentages = [round(item['total'] / total_geral * 100, 2) for item in qs]
        labels_bar = [item['mes'].strftime('%b/%Y') for item in qs_mensal]
        data_bar = [item['total'] for item in qs_mensal]

        context = {
            'labels': labels,
            'data': data,
            'percentages': percentages,
            'labels_bar': labels_bar,
            'data_bar': data_bar,
        }
        
        # Top 10 procedimentos com mais pacientes --------------
        qs_proc_count = (
            ListaEsperaCirurgica.objects
            .values('procedimento__nome')
            .annotate(total=Count('id'))
            .order_by('-total')[:10]
        )
        labels_proc_count = [i['procedimento__nome'] for i in qs_proc_count]
        data_proc_count   = [i['total'] for i in qs_proc_count]

        #  Top 10 procedimentos com maior tempo de espera -------
        qs_proc_wait = (
            ListaEsperaCirurgica.objects
            .values('procedimento__nome')
            .annotate(first_dt=Min('data_entrada'))
        )
        # converte em lista de tuplas (nome, dias_espera) e ordena
        today = now()
        wait_list = [
            (i['procedimento__nome'], (today - i['first_dt']).days)
            for i in qs_proc_wait if i['first_dt'] is not None
        ]
        wait_list.sort(key=lambda x: x[1], reverse=True)
        wait_list = wait_list[:10]                         # top-10
        labels_proc_wait = [w[0] for w in wait_list]
        data_proc_wait   = [w[1] for w in wait_list]

        context = {
            'labels': labels,
            'data': data,
            'percentages': percentages,
            'labels_bar': labels_bar,
            'data_bar': data_bar,
            # novos conjuntos
            'labels_proc_count': labels_proc_count,
            'data_proc_count': data_proc_count,
            'labels_proc_wait': labels_proc_wait,
            'data_proc_wait': data_proc_wait,
        }
        return TemplateResponse(
            request,
            self.change_list_template,
            {**self.admin_site.each_context(request), **context},
        )


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
    
@admin.action(description="Inserir entrada em campanha")
def add_campanha(modeladmin, request, queryset):
    queryset.update(campanha=True)

@admin.action(description="Remover entrada de campanha")
def remove_campanha(modeladmin, request, queryset):
    queryset.update(campanha=False)

class RemoverDaFilaForm(forms.Form):
    motivo = forms.ChoiceField(
        label="Selecione o motivo da remoção",
        choices=ListaEsperaCirurgica.MOTIVO_SAIDA_CHOICES,
        required=True,
        widget=forms.Select(attrs={"class": "form-control"})
    )

class RemoverDaFilaView(UnfoldModelAdminViewMixin, FormView):
    # Título que aparecerá no cabeçalho da página
    title = "Remover Pacientes da Fila"
    
    # Permissão necessária para acessar esta view
    permission_required = 'sua_app.change_listaesperacirurgica'
    
    # Template a ser renderizado
    template_name = "admin/remover_da_fila.html"
    
    # Classe do formulário a ser utilizada
    form_class = RemoverDaFilaForm

    def get_context_data(self, **kwargs):
        """Adiciona os pacientes selecionados ao contexto do template."""
        context = super().get_context_data(**kwargs)
        ids = self.request.GET.get('ids', '').split(',')
        # Usa o queryset do model_admin para respeitar filtros, se houver
        queryset = self.model_admin.get_queryset(self.request).filter(pk__in=ids)
        context['pacientes'] = queryset
        return context

    def form_valid(self, form):
        """Processa o formulário quando os dados são válidos."""
        motivo = form.cleaned_data['motivo']
        ids = self.request.GET.get('ids', '').split(',')
        queryset = self.model_admin.get_queryset(self.request).filter(pk__in=ids)
        
        count = queryset.count()
        queryset.update(ativo=False, motivo_saida=motivo)
        
        # Linha correta
        self.model_admin.message_user(self.request, f"{count} pacientes removidos da fila com sucesso.", messages.SUCCESS)
        
        # Redireciona de volta para a lista de registros (changelist)
        changelist_url = reverse(
            f'admin:{self.model_admin.model._meta.app_label}_{self.model_admin.model._meta.model_name}_changelist'
        )
        return HttpResponseRedirect(changelist_url)

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

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['change_reason'].widget = forms.TextInput(attrs={
            "class": (
                "border border-base-200 bg-white font-medium min-w-20 placeholder-base-400 rounded shadow-sm "
                "text-font-default-light text-sm focus:ring focus:ring-primary-300 focus:border-primary-600 "
                "focus:outline-none group-[.errors]:border-red-600 group-[.errors]:focus:ring-red-200 "
                "dark:bg-base-900 dark:border-base-700 dark:text-font-default-dark dark:focus:border-primary-600 "
                "dark:focus:ring-primary-700 dark:focus:ring-opacity-50 dark:group-[.errors]:border-red-500 "
                "dark:group-[.errors]:focus:ring-red-600/40 px-3 py-2 w-full max-w-2xl"
            ),
            "placeholder": "Motivo da alteração"
        })
        return form

    def save_model(self, request, obj, form, change):
        obj._change_reason = form.cleaned_data["change_reason"]
        super().save_model(request, obj, form, change)

    
    list_display = ('paciente', 'procedimento', 'especialidade', 'ativo')
    actions = ['remover_da_fila']

    def get_urls(self):
        """Registra a URL da view customizada."""
        urls = super().get_urls()
        
        # O nome da URL é construído dinamicamente para evitar conflitos
        url_name = f'{self.model._meta.app_label}_{self.model._meta.model_name}_remover_da_fila'

        # Admin_view protege a view com as permissões do admin
        custom_view = self.admin_site.admin_view(
            RemoverDaFilaView.as_view(
                model_admin=self # Passa a instância do admin para a view
            )
        )

        custom_urls = [
            path(
                'remover-da-fila/',
                custom_view,
                name=url_name,
            ),
        ]
        return custom_urls + urls

    def remover_da_fila(self, request, queryset):
        selected = queryset.values_list('pk', flat=True)
        return redirect(f'./remover-da-fila/?ids={",".join(str(pk) for pk in selected)}')

    remover_da_fila.short_description = "Remover da fila com justificativa"

    @admin.action(description="Remover da fila com justificativa")
    def remover_da_fila_action(self, request, queryset):
        """Ação que coleta os IDs e redireciona para a view de remoção."""
        selected_pks = queryset.values_list('pk', flat=True)
        
        # Usa 'reverse' para obter a URL de forma segura
        url_name = f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_remover_da_fila'
        redirect_url = reverse(url_name)
        
        # Adiciona os IDs como parâmetro na URL
        return HttpResponseRedirect(f'{redirect_url}?ids={",".join(map(str, selected_pks))}')


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

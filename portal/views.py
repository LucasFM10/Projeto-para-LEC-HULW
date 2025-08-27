from django.shortcuts import render

# Create your views here.
from typing import Dict, Any, List, Tuple
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin
from django.views.generic import TemplateView, DetailView, CreateView, UpdateView
from django_filters.views import FilterView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils.timezone import now

# Importa seu modelo real
from fila_cirurgica.models import ListaEsperaCirurgica

# Tenta reaproveitar o seu ModelForm oficial; cai para um fallback se não existir
try:
    from fila_cirurgica.forms import ListaEsperaCirurgicaForm as BaseListaEsperaForm
except Exception:
    from django import forms

    class BaseListaEsperaForm(forms.ModelForm):
        """Fallback simples caso o form oficial não esteja disponível no import.
        Ajuste fields/widgets conforme sua necessidade, evitando quebrar validações.
        """
        class Meta:
            model = ListaEsperaCirurgica
            fields = "__all__"
            widgets = {
                # Exemplo de widgets com classes Tailwind
                # Ajuste conforme os nomes reais dos campos
            }

# Constantes para nomes de campos (fácil de ajustar se divergirem)
CAMPO_ATIVO = "ativo"
CAMPO_JUDICIAL = "medida_judicial"
CAMPO_PRIORIDADE = "prioridade"
CAMPO_DATA_ENTRADA = "data_entrada"
REL_ESPECIALIDADE_NOME = "especialidade__nome_especialidade"
REL_PROCEDIMENTO_NOME = "procedimento__nome"
REL_MEDICO_NOME = "medico__nome"
REL_PACIENTE_PRONTUARIO = "paciente__prontuario"


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Exige usuário autenticado e staff."""
    def test_func(self) -> bool:
        return self.request.user.is_active and self.request.user.is_staff


class DashboardView(StaffRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Dashboard sem dados pessoais (apenas agregados)."""
    permission_required = "fila_cirurgica.view_listaesperacirurgica"
    template_name = "portal/dashboard.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        qs = ListaEsperaCirurgica.objects.all()

        total_ativos = qs.filter(**{CAMPO_ATIVO: True}).count()
        total_especialidades = (
            qs.exclude(especialidade__isnull=True)
              .values("especialidade_id")
              .distinct()
              .count()
        )
        total_procedimentos = (
            qs.exclude(procedimento__isnull=True)
              .values("procedimento_id")
              .distinct()
              .count()
        )
        ctx.update({
            "kpi_total_ativos": total_ativos,
            "kpi_total_especialidades": total_especialidades,
            "kpi_total_procedimentos": total_procedimentos,
            "agora": now(),
        })
        return ctx


from .filters import FilaFilter


class FilaListView(StaffRequiredMixin, PermissionRequiredMixin, FilterView):
    """Lista com filtros e paginação."""
    permission_required = "fila_cirurgica.view_listaesperacirurgica"
    model = ListaEsperaCirurgica
    filterset_class = FilaFilter
    paginate_by = 20
    template_name = "portal/fila_list.html"
    context_object_name = "objetos"

    def get_queryset(self):
        # Otimiza relacionamentos para evitar N+1
        return (
            ListaEsperaCirurgica.objects
            .select_related("paciente", "especialidade", "procedimento", "medico")
            .order_by("-" + CAMPO_DATA_ENTRADA)
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["hoje"] = now().date()
        return ctx


class FilaDetailView(StaffRequiredMixin, PermissionRequiredMixin, DetailView):
    permission_required = "fila_cirurgica.view_listaesperacirurgica"
    model = ListaEsperaCirurgica
    template_name = "portal/fila_detail.html"
    context_object_name = "obj"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        obj = ctx["obj"]

        # Posição na fila (usa método se existir)
        posicao = None
        if hasattr(obj, "get_posicao") and callable(obj.get_posicao):
            try:
                posicao = obj.get_posicao()
            except Exception:
                posicao = None
        ctx["posicao"] = posicao
        return ctx


class FilaCreateView(StaffRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "fila_cirurgica.add_listaesperacirurgica"
    model = ListaEsperaCirurgica
    form_class = BaseListaEsperaForm
    template_name = "portal/fila_form.html"
    success_url = reverse_lazy("portal:fila_list")


class FilaUpdateView(StaffRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "fila_cirurgica.change_listaesperacirurgica"
    model = ListaEsperaCirurgica
    form_class = BaseListaEsperaForm
    template_name = "portal/fila_form.html"
    success_url = reverse_lazy("portal:fila_list")

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        obj = getattr(self, "object", None)
        # Se inativo, torna read-only
        if obj and not getattr(obj, CAMPO_ATIVO, True):
            for f in form.fields.values():
                f.disabled = True
            messages.info(self.request, "Este registro está inativo — formulário em modo de visualização.")
        return form

    def form_valid(self, form):
        obj = form.instance
        # Se inativo, não permite salvar mudanças
        if obj and not getattr(obj, CAMPO_ATIVO, True):
            messages.warning(self.request, "Registro inativo. Alterações não foram salvas.")
            return self.form_invalid(form)
        return super().form_valid(form)


class FilaHistoryView(StaffRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Histórico estilo admin usando django-simple-history."""
    permission_required = "fila_cirurgica.view_listaesperacirurgica"
    template_name = "portal/fila_history.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        pk = self.kwargs.get("pk")
        obj = get_object_or_404(
            ListaEsperaCirurgica.objects.select_related("paciente", "especialidade", "procedimento", "medico"),
            pk=pk
        )
        history = obj.history.all().select_related("history_user").order_by("-history_date")

        # Constrói linhas com diff amigável (comparando com o registro anterior)
        linhas = []
        prev = None
        for h in history:
            diffs: List[Tuple[str, Any, Any]] = []
            if prev:
                diffs = self._diff_records(prev, h)
            linhas.append({
                "data": h.history_date,
                "usuario": getattr(h, "history_user", None),
                "tipo": {"+" : "Criado", "~": "Alterado", "-" : "Deletado"}.get(h.history_type, h.history_type),
                "motivo": getattr(h, "history_change_reason", "") or getattr(h, "change_reason", ""),
                "diffs": diffs,
            })
            prev = h
        ctx.update({"obj": obj, "linhas": linhas})
        return ctx

    def _diff_records(self, old, new) -> List[Tuple[str, Any, Any]]:
        """Compara campos simples, incluindo FK por string, e retorna lista (campo, antes, depois)."""
        diffs = []
        model = new.instance._meta
        # ignora campos de controle do simple_history
        ignore = {"id", "history_id", "history_date", "history_type", "history_user", "history_change_reason"}
        for field in model.fields:
            name = field.name
            if name in ignore:
                continue
            try:
                before = getattr(old, name, None)
                after = getattr(new, name, None)
                # Converte FKs para string amigável
                if getattr(field, "many_to_one", False) and hasattr(field, "remote_field"):
                    before = str(before) if before is not None else ""
                    after = str(after) if after is not None else ""
                if before != after:
                    diffs.append((name, before, after))
            except Exception:
                # Falha silenciosa em campo problemático
                continue
        return diffs

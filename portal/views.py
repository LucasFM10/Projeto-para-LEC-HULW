# portal/views.py
from __future__ import annotations

from datetime import timedelta
from django.db.models.functions import TruncMonth
from typing import Any, Dict, List, Tuple

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Min
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views.decorators.http import require_GET
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView, FormView
from django_filters.views import FilterView

from fila_cirurgica.models import ListaEsperaCirurgica
from portal.forms import PortalCreateFormLight
from .filters import FilaFilter

# Campos relacionais úteis (para evitar "string solta" no código)
REL_ESPECIALIDADE_NOME = "especialidade__nome_especialidade"
REL_PROCEDIMENTO_NOME = "procedimento__nome"
REL_MEDICO_NOME = "medico__nome"
REL_PACIENTE_PRONTUARIO = "paciente__prontuario"

CAMPO_ATIVO = "ativo"

# portal/views.py
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import UpdateView
from simple_history.utils import update_change_reason

from fila_cirurgica.models import ListaEsperaCirurgica

# --------------------- Mixins ---------------------
class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Exige usuário autenticado e staff."""
    def test_func(self) -> bool:
        return self.request.user.is_active and self.request.user.is_staff

from fila_cirurgica.models import ListaEsperaCirurgica
from .forms import FilaDeactivateForm, FilaUpdateForm

class FilaUpdateView(StaffRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "fila_cirurgica.change_listaesperacirurgica"
    model = ListaEsperaCirurgica
    form_class = FilaUpdateForm
    template_name = "portal/fila_update.html"   # novo template abaixo
    success_url = reverse_lazy("portal:fila_list")

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        # Caso o registro esteja inativo, travamos tudo
        obj = getattr(self, "object", None)
        if obj and not getattr(obj, "ativo", True):
            for fname, field in form.fields.items():
                field.disabled = True
                field.widget.attrs["class"] = (field.widget.attrs.get("class", "") + " bg-gray-50 cursor-not-allowed").strip()
        return form
    

    def form_valid(self, form):
        # Salva alterações permitidas
        response = super().form_valid(form)

        # Registra motivo no histórico (django-simple-history)
        motivo = form.cleaned_data.get("motivo_alteracao")
        if motivo:
            try:
                update_change_reason(self.object, motivo)
            except Exception:
                # não quebra a UX caso o simple-history não esteja disponível
                pass

        messages.success(self.request, "Entrada atualizada com sucesso.")
        return response
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        exclude = ["ativo", "motivo_saida"]
        ctx["exclude_fields"] = exclude
        print(ctx)
        return ctx


# --------------------- Dashboard ---------------------
from datetime import timedelta
from django.db.models import Count, Min
from django.db.models.functions import TruncMonth
from django.utils.timezone import now

class DashboardView(StaffRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Dashboard sem dados pessoais (apenas agregados)."""
    permission_required = "fila_cirurgica.view_listaesperacirurgica"
    template_name = "portal/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Período ~3 meses p/ série mensal (1º dia do mês atual - 60 dias)
        hoje = now().date()
        inicio_periodo = hoje.replace(day=1) - timedelta(days=60)

        # Base "na fila" = somente ativos
        ativos = ListaEsperaCirurgica.objects.filter(ativo=True)

        # KPIs principais (atuais, só ativos)
        pacientes_na_fila = ativos.values("paciente_id").distinct().count()
        especialidades_na_fila = ativos.values("especialidade_id").distinct().count()
        procedimentos_na_fila = ativos.values("procedimento_id").distinct().count()

        # Recortes
        count_eletivos = ativos.filter(prioridade="SEM", medida_judicial=False).count()
        count_oncologicos = ativos.filter(prioridade="ONC").count()
        count_judicializados = ativos.filter(medida_judicial=True).count()

        # Gráfico de pizza — distribuição por especialidade (apenas ativos)
        dist_qs = (
            ativos.values("especialidade__nome_especialidade")
                  .annotate(total=Count("id"))
                  .order_by("especialidade__nome_especialidade")
        )
        labels = [row["especialidade__nome_especialidade"] or "—" for row in dist_qs]
        data = [row["total"] for row in dist_qs]
        total_geral = sum(data) or 1
        percentages = [round((v / total_geral) * 100, 2) for v in data]

        # Barras — entradas criadas no período (todas as entradas, ativas ou não)
        mensal_qs = (
            ListaEsperaCirurgica.objects
            .filter(data_entrada__date__gte=inicio_periodo)
            .annotate(mes=TruncMonth("data_entrada"))
            .values("mes")
            .annotate(total=Count("id"))
            .order_by("mes")
        )
        labels_bar = [row["mes"].strftime("%b/%Y") for row in mensal_qs]
        data_bar = [row["total"] for row in mensal_qs]

        # Top 10 procedimentos com mais pacientes (apenas ativos)
        proc_count_qs = (
            ativos.values("procedimento__nome")
                  .annotate(total=Count("id"))
                  .order_by("-total")[:10]
        )
        labels_proc_count = [row["procedimento__nome"] or "—" for row in proc_count_qs]
        data_proc_count = [row["total"] for row in proc_count_qs]

        # Top 10 maior tempo de espera (dias) por procedimento (apenas ativos)
        first_dt_qs = (
            ativos.values("procedimento__nome")
                  .annotate(first_dt=Min("data_entrada"))
        )
        hoje_dt = now()
        wait_list = [
            (
                row["procedimento__nome"] or "—",
                (hoje_dt - row["first_dt"]).days if row["first_dt"] else 0,
            )
            for row in first_dt_qs if row["first_dt"] is not None
        ]
        wait_list.sort(key=lambda x: x[1], reverse=True)
        wait_list = wait_list[:10]
        labels_proc_wait = [name for name, _ in wait_list]
        data_proc_wait = [days for _, days in wait_list]

        # Contexto final (NÃO sobrescrever ctx!)
        ctx.update({
            # métricas principais
            "pacientes_na_fila": pacientes_na_fila,
            "especialidades_na_fila": especialidades_na_fila,
            "procedimentos_na_fila": procedimentos_na_fila,
            "count_eletivos": count_eletivos,
            "count_oncologicos": count_oncologicos,
            "count_judicializados": count_judicializados,

            # gráficos
            "labels": labels,
            "data": data,
            "percentages": percentages,
            "labels_bar": labels_bar,
            "data_bar": data_bar,
            "labels_proc_count": labels_proc_count,
            "data_proc_count": data_proc_count,
            "labels_proc_wait": labels_proc_wait,
            "data_proc_wait": data_proc_wait,

            # timestamp p/ footer
            "agora": now(),
        })
        return ctx


# --------------------- Lista / Filtros ---------------------
class FilaListView(StaffRequiredMixin, PermissionRequiredMixin, FilterView):
    """Lista com filtros e paginação."""
    permission_required = "fila_cirurgica.view_listaesperacirurgica"
    model = ListaEsperaCirurgica
    filterset_class = FilaFilter
    paginate_by = 10
    template_name = "portal/fila_list.html"
    context_object_name = "objetos"

    def get_queryset(self):
        """
        - Usa o manager .ordered() (seu model já provê) para manter a ordenação por prioridade,
          depois data_entrada, etc.
        - select_related para evitar N+1.
        """
        try:
            base = ListaEsperaCirurgica.objects.ordered()
        except AttributeError:
            base = ListaEsperaCirurgica.objects.all()
        return (
            base.select_related("paciente", "especialidade", "procedimento", "medico")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["hoje"] = now().date()
        return ctx


# --------------------- CRUD ---------------------
class FilaDetailView(StaffRequiredMixin, PermissionRequiredMixin, DetailView):
    permission_required = "fila_cirurgica.view_listaesperacirurgica"
    model = ListaEsperaCirurgica
    template_name = "portal/fila_detail.html"
    context_object_name = "obj"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        obj = ctx["obj"]
        # Posição na fila (se existir método utilitário no model)
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
    form_class = PortalCreateFormLight  # cria a partir dos IDs vindos da API (paciente/esp/proc/med)
    template_name = "portal/fila_form.html"
    success_url = reverse_lazy("portal:fila_list")

    def form_valid(self, form):
        obj = form.save(commit=True)
        update_change_reason(obj, "Criado via Portal")
        messages.success(self.request, "Entrada criada com sucesso.")
        return redirect(self.success_url)


# Fallback para edição: tenta usar o form do app principal, senão usa um básico
try:
    from fila_cirurgica.forms import ListaEsperaCirurgicaForm as BaseListaEsperaForm  # type: ignore
except Exception:
    from django import forms as _forms  # fallback

    class BaseListaEsperaForm(_forms.ModelForm):  # type: ignore
        class Meta:
            model = ListaEsperaCirurgica
            fields = "__all__"

# portal/forms.py
from django import forms
from fila_cirurgica.models import ListaEsperaCirurgica

# --------------------- Histórico ---------------------
from django.utils.timezone import localtime

class FilaHistoryView(StaffRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Exibe diffs a partir do django-simple-history."""
    permission_required = "fila_cirurgica.view_listaesperacirurgica"
    template_name = "portal/fila_history.html"

    _IGNORE = {"id", "history_id", "history_date", "history_type",
               "history_user", "history_change_reason"}

    def _to_display(self, field, value):
        """Formata valor para exibição (choices, FK, bool, datas)."""
        if value is None:
            return ""
        # choices -> rótulo
        if getattr(field, "choices", None):
            return dict(field.choices).get(value, value)
        # FK -> string amigável
        if getattr(field, "many_to_one", False) and hasattr(field, "remote_field"):
            return str(value) if value else ""
        # boolean
        from django.db.models import BooleanField
        if isinstance(field, BooleanField):
            return "Sim" if bool(value) else "Não"
        # datas
        from django.db.models import DateTimeField, DateField
        if isinstance(field, DateTimeField):
            return localtime(value).strftime("%d/%m/%Y %H:%M") if value else ""
        if isinstance(field, DateField):
            return value.strftime("%d/%m/%Y") if value else ""
        return value

    def _diff_records(self, older, newer):
        """Retorna [(verbose_name, antes, depois)] apenas dos campos que mudaram."""
        if not older or not newer:
            return []
        model_meta = newer.instance._meta
        diffs = []
        for field in model_meta.fields:
            name = field.name
            if name in self._IGNORE:
                continue
            before = getattr(older, name, None)
            after = getattr(newer, name, None)
            if before == after:
                continue
            diffs.append((
                field.verbose_name or name,
                self._to_display(field, before),
                self._to_display(field, after),
            ))
        return diffs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj = get_object_or_404(ListaEsperaCirurgica, pk=self.kwargs.get("pk"))

        # ordem decrescente (mais recente primeiro)
        history = obj.history.select_related("history_user").order_by("-history_date")

        linhas = []
        for idx, h in enumerate(history):
            older = history[idx + 1] if (idx + 1) < history.count() else None
            diffs = self._diff_records(older, h)
            linhas.append({
                "data": h.history_date,
                "usuario": getattr(h, "history_user", None),
                "tipo": {"+": "Criado", "~": "Alterado", "-": "Deletado"}.get(h.history_type, h.history_type),
                "motivo": getattr(h, "history_change_reason", "") or getattr(h, "change_reason", ""),
                "diffs": diffs,
            })

        ctx["obj"] = obj
        ctx["linhas"] = linhas
        return ctx


# --------------------- APIs auxiliares ---------------------
@require_GET
def paciente_api_validate(request):
    """
    Valida um prontuário na API externa e retorna {valid: bool, nome?: str}.
    Usado no formulário leve de criação.
    """
    prontuario = request.GET.get("prontuario")
    if not prontuario:
        return JsonResponse({"valid": False, "error": "prontuario ausente"}, status=400)

    base = getattr(settings, "API_BASE_URL", "").rstrip("/")
    if not base:
        return JsonResponse({"valid": False, "error": "API_BASE_URL não configurada"}, status=500)

    url = f"{base}/api/v1/pacientes/{prontuario}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 404:
            return JsonResponse({"valid": False})
        r.raise_for_status()
        data = r.json()
        nome = data.get("nome") or data.get("NOME") or data.get("nome_paciente")
        return JsonResponse({"valid": True, "nome": nome})
    except requests.RequestException:
        return JsonResponse({"valid": False, "error": "falha na API"}, status=502)

class FilaDeactivateView(StaffRequiredMixin, PermissionRequiredMixin, FormView):
    """
    “Excluir” do portal: não deleta, apenas marca ativo=False e registra motivo no histórico.
    """
    permission_required = "fila_cirurgica.change_listaesperacirurgica"
    template_name = "portal/confirm_remove.html"
    form_class = FilaDeactivateForm
    success_url = reverse_lazy("portal:fila_list")

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(ListaEsperaCirurgica, pk=kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["obj"] = self.object
        print(ctx)
        return ctx

    def form_valid(self, form):
        motivo = form.cleaned_data["motivo"]               # value dos choices (igual ao Admin)
        change_reason = form.cleaned_data["change_reason"] # texto livre (vai pro histórico)
        
        obj = self.object

        # ⬇️ mesmo comportamento do Admin: atualiza o PRÓPRIO objeto e inativa
        obj.ativo = False
        obj.motivo_saida = motivo
        obj.save(update_fields=["ativo", "motivo_saida"])

        # ⬇️ histórico recebe apenas a justificativa (como no Admin)
        try:
            update_change_reason(obj, change_reason)
        except Exception:
            pass

        from django.contrib import messages
        messages.success(self.request, f"{obj} removido(s) da fila com sucesso.")

        return redirect(self.get_success_url())
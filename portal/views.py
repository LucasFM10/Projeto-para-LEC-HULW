# portal/views.py
from __future__ import annotations

from typing import Any, Dict, List, Tuple

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views.decorators.http import require_GET
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView
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


# --------------------- Mixins ---------------------
class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Exige usuário autenticado e staff."""
    def test_func(self) -> bool:
        return self.request.user.is_active and self.request.user.is_staff


# --------------------- Dashboard ---------------------
class DashboardView(StaffRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Dashboard sem dados pessoais (apenas agregados)."""
    permission_required = "fila_cirurgica.view_listaesperacirurgica"
    template_name = "portal/dashboard.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        # KPIs simples (você pode ajustar conforme a necessidade)
        qs = ListaEsperaCirurgica.objects.all()
        ctx.update(
            kpi_total=qs.count(),
            kpi_total_ativos=qs.filter(ativo=True).count(),
            kpi_total_especialidades=qs.values("especialidade").distinct().count(),
            kpi_total_procedimentos=qs.values("procedimento").distinct().count(),
            agora=now(),
        )
        return ctx


# --------------------- Lista / Filtros ---------------------
class FilaListView(StaffRequiredMixin, PermissionRequiredMixin, FilterView):
    """Lista com filtros e paginação."""
    permission_required = "fila_cirurgica.view_listaesperacirurgica"
    model = ListaEsperaCirurgica
    filterset_class = FilaFilter
    paginate_by = 20
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


class FilaUpdateView(StaffRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "fila_cirurgica.change_listaesperacirurgica"
    model = ListaEsperaCirurgica
    form_class = BaseListaEsperaForm
    template_name = "portal/fila_form.html"
    success_url = reverse_lazy("portal:fila_list")

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        obj = getattr(self, "object", None)
        # Se inativo, torna todos read-only
        if obj and not getattr(obj, CAMPO_ATIVO, True):
            for f in form.fields.values():
                f.disabled = True
        return form

    def form_valid(self, form):
        obj = getattr(self, "object", None)
        if obj and not getattr(obj, CAMPO_ATIVO, True):
            messages.warning(self.request, "Registro inativo. Alterações não foram salvas.")
            return self.form_invalid(form)
        return super().form_valid(form)


class FilaHistoryView(StaffRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Exibe diffs a partir do django-simple-history."""
    permission_required = "fila_cirurgica.view_listaesperacirurgica"
    template_name = "portal/fila_history.html"

    def _diff_records(self, old, new) -> List[Tuple[str, Any, Any]]:
        diffs: List[Tuple[str, Any, Any]] = []
        model = new.instance._meta
        ignore = {"id", "history_id", "history_date", "history_type", "history_user", "history_change_reason"}
        for field in model.fields:
            name = field.name
            if name in ignore:
                continue
            before = getattr(old, name, None)
            after = getattr(new, name, None)
            # FKs impressas como string amigável
            if getattr(field, "many_to_one", False) and hasattr(field, "remote_field"):
                before = str(before) if before is not None else ""
                after = str(after) if after is not None else ""
            diffs.append((field.verbose_name or name, before, after))
        return diffs

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        pk = self.kwargs.get("pk")
        obj = get_object_or_404(ListaEsperaCirurgica, pk=pk)
        history = obj.history.order_by("-history_date")
        linhas = []
        prev = None
        for h in history:
            diffs = self._diff_records(prev, h) if prev else []
            linhas.append(
                {
                    "data": h.history_date,
                    "usuario": getattr(h, "history_user", None),
                    "tipo": {"+": "Criado", "~": "Alterado", "-": "Deletado"}.get(h.history_type, h.history_type),
                    "motivo": getattr(h, "history_change_reason", "") or getattr(h, "change_reason", ""),
                    "diffs": diffs,
                }
            )
            prev = h
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

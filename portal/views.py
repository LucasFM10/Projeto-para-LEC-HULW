from __future__ import annotations

from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView, DetailView, CreateView, UpdateView
from django_filters.views import FilterView

from fila_cirurgica.models import ListaEsperaCirurgica
from fila_cirurgica.api_helpers import (
    get_or_create_paciente,
    get_or_create_procedimento,
    get_or_create_especialidade,
    get_or_create_profissional,
)
from simple_history.utils import update_change_reason

from .forms import PortalListaEsperaForm
from .filters import FilaFilter as FilaFilterSet


# ---------- Mixins ----------
class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self) -> bool:
        return bool(self.request.user and self.request.user.is_staff)


# ---------- Dashboard ----------
class DashboardView(StaffRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "portal/dashboard.html"
    permission_required = "fila_cirurgica.view_listaesperacirurgica"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        qs = ListaEsperaCirurgica.objects.select_related("especialidade", "procedimento").filter(ativo=True)
        ctx["indicadores"] = {
            "na_fila": qs.count(),
            "especialidades": qs.values("especialidade_id").distinct().count(),
            "procedimentos": qs.values("procedimento_id").distinct().count(),
        }
        return ctx


# ---------- List ----------
class FilaListView(StaffRequiredMixin, PermissionRequiredMixin, FilterView):
    model = ListaEsperaCirurgica
    template_name = "portal/fila_list.html"
    context_object_name = "objetos"
    paginate_by = 20
    permission_required = "fila_cirurgica.view_listaesperacirurgica"
    filterset_class = FilaFilterSet

    def get_queryset(self):
        return (
            ListaEsperaCirurgica.objects.select_related(
                "paciente", "especialidade", "procedimento", "medico"
            )
            .all()
            .order_by("-data_entrada")
        )


# ---------- Create ----------
class FilaCreateView(StaffRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ListaEsperaCirurgica
    template_name = "portal/fila_form.html"
    permission_required = "fila_cirurgica.add_listaesperacirurgica"
    form_class = PortalListaEsperaForm
    success_url = reverse_lazy("portal:fila_list")

    def form_valid(self, form):
        inst = form.instance

        # IDs vindos do template
        prontuario = form.cleaned_data.get("prontuario")
        esp_id = form.cleaned_data.get("especialidade_id") or None
        proc_id = form.cleaned_data.get("procedimento_id") or None
        med_mat = form.cleaned_data.get("medico_matricula") or None

        try:
            inst.paciente = get_or_create_paciente(prontuario)
            if esp_id:
                inst.especialidade = get_or_create_especialidade(esp_id)
            if proc_id:
                inst.procedimento = get_or_create_procedimento(proc_id)
            if med_mat:
                inst.medico = get_or_create_profissional(med_mat)
        except Exception as e:
            form.add_error(None, f"Falha ao contatar a API: {e}")
            return self.form_invalid(form)

        # histórico
        inst._history_user = self.request.user
        resp = super().form_valid(form)
        reason = form.cleaned_data.get("change_reason")
        if reason:
            update_change_reason(self.object, reason)

        messages.success(self.request, "Entrada criada com sucesso.")
        return resp


# ---------- Update ----------
class FilaUpdateView(StaffRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ListaEsperaCirurgica
    template_name = "portal/fila_form.html"
    permission_required = "fila_cirurgica.change_listaesperacirurgica"
    form_class = PortalListaEsperaForm
    success_url = reverse_lazy("portal:fila_list")

    def get_initial(self):
        init = super().get_initial()
        obj = self.get_object()
        if getattr(obj, "paciente", None) and getattr(obj.paciente, "prontuario", None):
            init["prontuario"] = obj.paciente.prontuario
        if getattr(obj, "especialidade_id", None):
            init["especialidade_id"] = str(obj.especialidade_id)
        if getattr(obj, "procedimento_id", None):
            init["procedimento_id"] = str(obj.procedimento_id)
        if getattr(obj, "medico", None) and getattr(obj.medico, "matricula", None):
            init["medico_matricula"] = str(obj.medico.matricula)
        return init

    def form_valid(self, form):
        # Se inativo, apenas bloqueia salvar (UI já desabilita, mas garantimos aqui)
        if self.object and getattr(self.object, "ativo", True) is False:
            messages.warning(self.request, "Registro inativo — alterações não foram salvas.")
            return self.form_invalid(form)

        inst = form.instance
        prontuario = form.cleaned_data.get("prontuario")
        esp_id = form.cleaned_data.get("especialidade_id") or None
        proc_id = form.cleaned_data.get("procedimento_id") or None
        med_mat = form.cleaned_data.get("medico_matricula") or None

        try:
            if prontuario:
                inst.paciente = get_or_create_paciente(prontuario)
            if esp_id:
                inst.especialidade = get_or_create_especialidade(esp_id)
            if proc_id:
                inst.procedimento = get_or_create_procedimento(proc_id)
            if med_mat:
                inst.medico = get_or_create_profissional(med_mat)
        except Exception as e:
            form.add_error(None, f"Falha ao contatar a API: {e}")
            return self.form_invalid(form)

        inst._history_user = self.request.user
        resp = super().form_valid(form)
        reason = form.cleaned_data.get("change_reason")
        if reason:
            update_change_reason(self.object, reason)

        messages.success(self.request, "Entrada atualizada com sucesso.")
        return resp


# ---------- Detail ----------
class FilaDetailView(StaffRequiredMixin, PermissionRequiredMixin, DetailView):
    model = ListaEsperaCirurgica
    template_name = "portal/fila_detail.html"
    permission_required = "fila_cirurgica.view_listaesperacirurgica"


# ---------- History ----------
class FilaHistoryView(StaffRequiredMixin, PermissionRequiredMixin, DetailView):
    model = ListaEsperaCirurgica
    template_name = "portal/fila_history.html"
    permission_required = "fila_cirurgica.view_listaesperacirurgica"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        obj = self.object
        history = obj.history.select_related("history_user").order_by("-history_date")

        def diff_fields(prev, curr):
            diffs = []
            if not prev:
                return diffs
            for field in [
                "prioridade", "medida_judicial", "situacao", "observacoes",
                "data_novo_contato", "ativo", "motivo_saida",
                "paciente_id", "especialidade_id", "procedimento_id", "medico_id",
            ]:
                try:
                    if getattr(prev, field) != getattr(curr, field):
                        diffs.append((field, getattr(prev, field), getattr(curr, field)))
                except Exception:
                    continue
            return diffs

        rows = []
        prev = None
        for h in history:
            rows.append({
                "date": h.history_date,
                "user": getattr(h.history_user, "get_username", lambda: None)() if h.history_user else "—",
                "type": getattr(h, "get_history_type_display", lambda: h.history_type)(),
                "reason": getattr(h, "history_change_reason", "") or "",
                "diffs": diff_fields(prev, h),
            })
            prev = h
        ctx["history_rows"] = rows
        return ctx

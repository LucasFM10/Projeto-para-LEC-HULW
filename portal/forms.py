from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from fila_cirurgica.models import ListaEsperaCirurgica

# Tente reutilizar o form original, mas caia para um ModelForm simples se não existir
try:
    from fila_cirurgica.forms import ListaEsperaCirurgicaForm as BaseListaEsperaForm  # type: ignore
except Exception:
    BaseListaEsperaForm = forms.ModelForm  # fallback


class PortalListaEsperaForm(BaseListaEsperaForm):
    """
    Form do Portal para CRIAÇÃO/EDIÇÃO consumindo a API.
    Os selects “bonitos” são feitos no template; aqui guardamos apenas os IDs.
    """
    prontuario = forms.CharField(
        label=_("Prontuário do Paciente"),
        help_text=_("Digite o número do prontuário (somente números)."),
        widget=forms.TextInput(attrs={
            "class": "w-full border rounded px-3 py-2",
            "inputmode": "numeric",
            "placeholder": "Ex.: 123456",
        })
    )

    # IDs vindos da API (preenchidos via JS no template)
    especialidade_id = forms.CharField(required=False, widget=forms.HiddenInput())
    procedimento_id = forms.CharField(required=False, widget=forms.HiddenInput())
    medico_matricula = forms.CharField(required=False, widget=forms.HiddenInput())

    # motivo (simple_history)
    change_reason = forms.CharField(
        label=_("Motivo da alteração"),
        required=False,
        widget=forms.TextInput(attrs={"class": "w-full border rounded px-3 py-2", "placeholder": "Opcional"})
    )

    class Meta:
        model = ListaEsperaCirurgica
        fields = [
            "prioridade",
            "medida_judicial",
            "situacao",
            "observacoes",
            "data_novo_contato",
        ]
        widgets = {
            "prioridade": forms.Select(attrs={"class": "w-full border rounded px-3 py-2"}),
            "medida_judicial": forms.Select(attrs={"class": "w-full border rounded px-3 py-2"}),
            "situacao": forms.Select(attrs={"class": "w-full border rounded px-3 py-2"}),
            "observacoes": forms.TextInput(attrs={"class": "w-full border rounded px-3 py-2", "placeholder": "Notas/observações"}),
            "data_novo_contato": forms.DateInput(attrs={"type": "date", "class": "w-full border rounded px-3 py-2"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Se vier instância inativa, bloqueia edição visual
        instance = getattr(self, "instance", None)
        if instance and hasattr(instance, "ativo") and instance.ativo is False:
            for f in self.fields.values():
                f.disabled = True

        # Se estiver em update, preencher iniciais (para o JS exibir rótulos)
        inst = getattr(self, "instance", None)
        if inst and inst.pk:
            if getattr(inst, "paciente", None) and getattr(inst.paciente, "prontuario", None):
                self.fields["prontuario"].initial = inst.paciente.prontuario
            if getattr(inst, "especialidade_id", None):
                self.fields["especialidade_id"].initial = str(inst.especialidade_id)
            if getattr(inst, "procedimento_id", None):
                self.fields["procedimento_id"].initial = str(inst.procedimento_id)
            if getattr(inst, "medico", None) and getattr(inst.medico, "matricula", None):
                self.fields["medico_matricula"].initial = str(inst.medico.matricula)

    def clean(self):
        cleaned = super().clean()

        esp = cleaned.get("especialidade_id") or ""
        proc = cleaned.get("procedimento_id") or ""

        # Procedimento depende de especialidade
        if proc and not esp:
            raise ValidationError(_("Selecione a especialidade antes do procedimento."))

        # Opcional: validar relação (se helper existir)
        try:
            from fila_cirurgica.api_helpers import validar_procedimento_na_especialidade
        except Exception:
            validar_procedimento_na_especialidade = None  # type: ignore

        if validar_procedimento_na_especialidade and esp and proc:
            ok = validar_procedimento_na_especialidade(proc, esp)
            if not ok:
                raise ValidationError(_("O procedimento informado não pertence à especialidade selecionada."))

        return cleaned

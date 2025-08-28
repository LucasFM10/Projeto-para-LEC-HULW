# portal/forms.py
from __future__ import annotations

from django import forms
from fila_cirurgica.api_helpers import (
    get_or_create_especialidade,
    get_or_create_paciente,
    get_or_create_procedimento,
    get_or_create_profissional,
)
from fila_cirurgica.models import ListaEsperaCirurgica


class PortalCreateFormLight(forms.ModelForm):
    """
    Form de criação leve para LEC.
    Os campos *_api são "fakes" (IDs vindos da API por AJAX) para popular os FKs reais
    (paciente, especialidade, procedimento, medico) no save().
    """

    # --- Campos "fake" controlados pelo front (Select2/AJAX) ---
    especialidade_api = forms.ChoiceField(
        label="Especialidade",
        required=False,
        choices=[("", "Digite para buscar…")],
        widget=forms.Select(attrs={"id": "id_especialidade_api"}),
    )
    procedimento_api = forms.ChoiceField(
        label="Procedimento",
        required=True,
        choices=[("", "Digite para buscar…")],
        widget=forms.Select(attrs={"id": "id_procedimento_api"}),
    )
    medico_api = forms.ChoiceField(
        label="Médico",
        required=True,
        choices=[("", "Digite para buscar…")],
        widget=forms.Select(attrs={"id": "id_medico_api"}),
    )

    prontuario = forms.ChoiceField(
        label="Prontuário",
        required=True,
        choices=[("", "Digite para buscar…")],
        widget=forms.Select(attrs={"id": "id_prontuario"}),
    )

    class Meta:
        model = ListaEsperaCirurgica
        fields = ["prioridade", "medida_judicial", "situacao", "observacoes"]
        widgets = {
            "medida_judicial": forms.CheckboxInput(attrs={"class": "h-4 w-4"}),
            "observacoes": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Observações…", "class": "w-full border rounded px-3 py-2"}
            ),
        }
        labels = {
            "prioridade": "Prioridade",
            "medida_judicial": "Medida judicial",
            "situacao": "Situação",
            "observacoes": "Observações",
        }
        help_texts = {
            "prioridade": "Selecione a prioridade conforme a regra do serviço.",
            "medida_judicial": "Marque se há decisão judicial aplicável.",
            "situacao": "Estado atual do paciente na fila.",
            "observacoes": "Anotações internas/observações livres.",
        }

    # ------------------------------
    # Inicialização e ajustes de UI
    # ------------------------------
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        def _ensure_choice(field_name: str) -> None:
            """
            Garante que o valor postado exista em `choices` para o Django validar.
            Sem isso, o POST '17' cai em "Faça uma escolha válida" porque o select
            é carregado por AJAX e o form não tem a lista no server-side.
            """
            field = self.fields[field_name]
            value = self.data.get(field_name) or self.initial.get(field_name)
            if not value:
                return

            # Opcional: se o front enviar também o label, aceitamos via *_text
            label = self.data.get(f"{field_name}_text") or str(value)

            # Evita duplicado e injeta o par (valor, rótulo)
            if not any(str(value) == str(v) for v, _ in field.choices):
                field.choices = list(field.choices) + [(str(value), label)]

        for name in ("especialidade_api", "procedimento_api", "medico_api", "prontuario"):
            _ensure_choice(name)

        # Estilo padrão Tailwind (evita repetir classes em cada field)
        for name, field in self.fields.items():
            if name in {"medida_judicial", "observacoes"}:
                continue
            current = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (current + " w-full border rounded px-3 py-2").strip()

        # Valor visual padrão (não altera regra de negócio)
        if "medida_judicial" in self.fields and self.initial.get("medida_judicial") is None:
            self.initial["medida_judicial"] = False

        # Ordem mais amigável no formulário
        desired_order = [
            "especialidade_api",
            "procedimento_api",
            "medico_api",
            "prontuario",
            "medida_judicial",
            "situacao",
            "prioridade",
            "observacoes",
        ]
        # Só reordena os que existem
        self.order_fields([f for f in desired_order if f in self.fields])

    # ------------------------------
    # Validação
    # ------------------------------
    def clean(self) -> dict:
        cleaned = super().clean()
        required = ("especialidade_api", "procedimento_api", "medico_api", "prontuario")
        missing = [r for r in required if not cleaned.get(r)]
        if missing:
            raise forms.ValidationError("Preencha todos os campos obrigatórios.")
        return cleaned

    # ------------------------------
    # Persistência
    # ------------------------------
    def save(self, commit: bool = True) -> ListaEsperaCirurgica:
        """
        Mapeia os IDs vindos dos campos *_api para os FKs reais do modelo via helpers
        e então salva a instância.
        """
        instance: ListaEsperaCirurgica = super().save(commit=False)

        prontuario = self.cleaned_data["prontuario"].strip()
        esp_id = str(self.cleaned_data["especialidade_api"])
        proc_id = str(self.cleaned_data["procedimento_api"])
        med_id = str(self.cleaned_data["medico_api"])

        # Helpers: buscam/criam registros locais a partir de IDs externos
        paciente = get_or_create_paciente(prontuario=prontuario)
        especialidade = get_or_create_especialidade(esp_id)
        procedimento = get_or_create_procedimento(proc_id)
        medico = get_or_create_profissional(med_id)

        instance.paciente = paciente
        instance.especialidade = especialidade
        instance.procedimento = procedimento
        instance.medico = medico

        if commit:
            instance.save()
        return instance

from __future__ import annotations

from django import forms
from fila_cirurgica.api_helpers import (
    get_or_create_especialidade,
    get_or_create_paciente,
    get_or_create_procedimento,
    get_or_create_profissional,
)
from fila_cirurgica.models import ListaEsperaCirurgica

class FilaUpdateForm(forms.ModelForm):
    """
    Edição: trava FK principais; exige motivo da alteração; mantém campos padronizados.
    """
    motivo_alteracao = forms.CharField(
        label="Motivo da alteração",
        required=True,
        widget=forms.Textarea(
            attrs={"rows": 3, "placeholder": "Explique o que mudou e por quê (obrigatório)."}),
    )

    # =================================================================
    # NOVOS CAMPOS JUDICIAIS
    # =================================================================
    judicial_numero = forms.CharField(
        label="Número do Processo Judicial",
        required=False,
        widget=forms.TextInput(attrs={"id": "id_judicial_numero"})
    )
    judicial_descricao = forms.CharField(
        label="Descrição da Medida Judicial",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "id": "id_judicial_descricao"})
    )
    judicial_anexos = forms.FileField(
        label="Anexar Documentos",
        required=False,
    )
    
    LOCKED_FIELDS = ("especialidade", "procedimento", "paciente", "medico")

    class Meta:
        model = ListaEsperaCirurgica
        fields = [
            "especialidade",
            "procedimento",
            "paciente",
            "medico",
            "prioridade",
            "medida_judicial",
            "situacao",
            "observacoes",
            "data_novo_contato",
            "motivo_alteracao",
            # Incluindo os novos campos
            "judicial_numero",
            "judicial_descricao",
            "judicial_anexos",
        ]
        widgets = {
            "medida_judicial": forms.CheckboxInput(attrs={"class": "h-4 w-4 text-indigo-600 border-gray-300 rounded"}),
            "observacoes": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Observações…",
                       "class": "w-full border rounded px-3 py-2"}
            ),
            "motivo_alteracao": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Alterações",
                       "class": "w-full border rounded px-3 py-2"}
            ),
            "data_novo_contato": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Ordem dos campos: Incluir os campos judiciais no fluxo
        desired = [
            "especialidade", "procedimento", "paciente", "medico", # Campos travados
            "prioridade", "medida_judicial",
            # Novos campos judiciais que serão movidos
            "judicial_numero", "judicial_descricao", "judicial_anexos",
            "situacao", "observacoes", "data_novo_contato", "motivo_alteracao"
        ]
        self.order_fields([f for f in desired if f in self.fields])

        # aceita 'YYYY-MM-DD' e 'DD/MM/YYYY' para o input de data (quando presente)
        if "data_novo_contato" in self.fields:
            self.fields["data_novo_contato"].input_formats = [
                "%Y-%m-%d", "%d/%m/%Y"]

        # oculta "motivo_alteracao" quando o registro estiver inativo
        if self.instance and not self.instance.ativo and "motivo_alteracao" in self.fields:
            self.fields.pop("motivo_alteracao")

        # trava FKs principais
        for name in self.LOCKED_FIELDS:
            if name in self.fields:
                self.fields[name].disabled = True
                self.fields[name].widget.attrs.update(
                    {
                        "readonly": True,
                        "class": (self.fields[name].widget.attrs.get("class", "") + " bg-gray-50 cursor-not-allowed").strip(),
                        "title": "Campo bloqueado na edição",
                    }
                )

    def clean(self):
        cleaned = super().clean()
        # ... (restante do clean, inalterado)
        
        # impede mudanças silenciosas via HTML nos campos travados
        for name in self.LOCKED_FIELDS:
            if name in self.changed_data:
                self.add_error(name, "Este campo não pode ser alterado.")
                cleaned[name] = getattr(self.instance, name)

        # exige motivo da alteração
        motivo = (cleaned.get("motivo_alteracao") or "").strip()
        if "motivo_alteracao" in self.fields and not motivo:
            self.add_error("motivo_alteracao",
                           "Informe o motivo da alteração.")
        return cleaned

class FilaCreateForm(forms.ModelForm):
    """
    Criação "leve" via IDs externos (Select2/AJAX). Campos *_api abastecem os FKs reais no save().
    """
    especialidade_api = forms.ChoiceField(
        label="Especialidade",
        required=True,
        choices=[("", "Digite para buscar…")],
        widget=forms.Select(attrs={"id": "id_especialidade_api"}),
    )
    procedimento_api = forms.ChoiceField(
        label="Procedimento",
        required=True,
        choices=[("", "Digite para buscar…")],
        widget=forms.Select(attrs={"id": "id_procedimento_api"}),
    )
    especialidade_secundario_api = forms.ChoiceField(
        label="Especialidade Secundária",
        required=False,  # CORRIGIDO: Deve ser opcional
        choices=[("", "Digite para buscar…")],
        widget=forms.Select(attrs={"id": "id_especialidade_secundario_api"}),
    )
    procedimento_secundario_api = forms.ChoiceField(
        label="Procedimento Secundário",
        required=False,  # CORRIGIDO: Deve ser opcional
        choices=[("", "Digite para buscar…")],
        widget=forms.Select(attrs={"id": "id_procedimento_secundario_api"}),
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
    secondary_section_open = forms.BooleanField(
        required=False, 
        widget=forms.HiddenInput()
    )

    judicial_numero = forms.CharField(
        label="Número do Processo Judicial",
        required=False,
        widget=forms.TextInput(attrs={"id": "id_judicial_numero"})
    )
    judicial_descricao = forms.CharField(
        label="Descrição da Medida Judicial",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "id": "id_judicial_descricao"})
    )
    judicial_anexos = forms.FileField(
        label="Anexos do Processo",
        required=False,
        widget=forms.FileInput(attrs={"id": "id_judicial_anexos"})
    )

    class Meta:
        model = ListaEsperaCirurgica
        fields = [
            "prioridade",
            "medida_judicial",
            "situacao",
            "observacoes",
            "secondary_section_open",
            # Adicionando os novos campos aqui
            "judicial_numero", 
            "judicial_descricao", 
            "judicial_anexos",
        ]
        widgets = {
            "medida_judicial": forms.CheckboxInput(
                attrs={"class": "h-4 w-4 text-indigo-600 border-gray-300 rounded", "id": "id_medida_judicial"}
            ),
            "observacoes": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Observações…",
                       "class": "w-full border rounded px-3 py-2"}
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

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        def ensure_choice(field_name: str) -> None:
            """
            Injeta a opção postada em `choices` para o Django validar selects AJAX.
            """
            field = self.fields[field_name]
            value = self.data.get(field_name) or self.initial.get(field_name)
            if not value:
                return
            label = self.data.get(f"{field_name}_text") or str(value)
            if not any(str(value) == str(v) for v, _ in field.choices):
                field.choices = list(field.choices) + [(str(value), label)]

        for name in (
            "especialidade_api", "procedimento_api", 
            "especialidade_secundario_api", "procedimento_secundario_api",
            "medico_api", "prontuario"
        ):
            ensure_choice(name)

        # estilo padrão (evita repetir classes em cada field)
        for name, field in self.fields.items():
            if name in {"medida_judicial", "observacoes", "judicial_anexos"}:
                continue
            current = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (
                current + " w-full border rounded px-3 py-2").strip()

        # ordem mais amigável
        desired = [
            "especialidade_api",
            "procedimento_api",
            "especialidade_secundario_api",
            "procedimento_secundario_api",
            "medico_api",
            "prontuario",
            "medida_judicial",
            "judicial_numero", 
            "judicial_descricao", 
            "judicial_anexos",
            "situacao",
            "prioridade",
            "observacoes",
        ]
        self.order_fields([f for f in desired if f in self.fields])

    def clean(self) -> dict:
        cleaned = super().clean()
        required = ("especialidade_api", "procedimento_api",
                    "medico_api", "prontuario")
        missing = [r for r in required if not cleaned.get(r)]
        if missing:
            raise forms.ValidationError(
                "Preencha todos os campos obrigatórios.")
        return cleaned

    def save(self, commit: bool = True) -> ListaEsperaCirurgica:
        """
        Converte IDs externos em FKs reais via helpers e salva.
        """
        instance: ListaEsperaCirurgica = super().save(commit=False)

        prontuario = self.cleaned_data["prontuario"].strip()
        esp_id = str(self.cleaned_data["especialidade_api"])
        proc_id = str(self.cleaned_data["procedimento_api"])
        med_id = str(self.cleaned_data["medico_api"])
        proc_sec_id = self.cleaned_data.get("procedimento_secundario_api")
        esp_sec_id = self.cleaned_data.get("especialidade_secundario_api")

        # helpers populam/retornam registros locais
        instance.paciente = get_or_create_paciente(prontuario=prontuario)
        instance.especialidade = get_or_create_especialidade(esp_id)
        instance.procedimento = get_or_create_procedimento(proc_id)
        instance.medico = get_or_create_profissional(med_id)

        if proc_sec_id and esp_sec_id:
            instance.procedimento_secundario = get_or_create_procedimento(proc_sec_id)
            instance.especialidade_secundario = get_or_create_especialidade(esp_sec_id)
        else:
            instance.procedimento_secundario = None
            instance.especialidade_secundario = None

        if commit:
            instance.save()
        return instance


class FilaDeactivateForm(forms.Form):
    """
    Remoção (inativação) no Portal: motivo pré-definido (choices do model) + justificativa.
    """
    motivo = forms.ChoiceField(
        label="Motivo da remoção",
        choices=(),  # preenchido dinamicamente com os choices do model
        required=True,
        widget=forms.RadioSelect,
    )
    change_reason = forms.CharField(
        label="Justificativa",
        required=True,
        widget=forms.Textarea(
            attrs={"rows": 3, "placeholder": "Descreva o contexto da remoção (obrigatório)."}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # puxa os choices do campo motivo_saida para manter em sincronia com o Admin
        try:
            field = ListaEsperaCirurgica._meta.get_field("motivo_saida")
            if getattr(field, "choices", None):
                self.fields["motivo"].choices = list(field.choices)
        except Exception:
            pass

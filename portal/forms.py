from __future__ import annotations

from django import forms
from django.urls import reverse_lazy  # Importado para resolver URLs no widget
from fila_cirurgica.api_helpers import (
    get_or_create_especialidade,
    get_or_create_paciente,
    get_or_create_procedimento,
    get_or_create_profissional,
)
from fila_cirurgica.models import ListaEsperaCirurgica


class FilaUpdateForm(forms.ModelForm):
    """
    Formulário para EDIÇÃO de uma entrada da fila.
    - Trava os campos-chave (FKs).
    - Exige um motivo para a alteração (compliance/histórico).
    """

    # Campo obrigatório para rastrear o motivo da alteração no histórico
    motivo_alteracao = forms.CharField(
        label="Motivo da alteração",
        required=True,
        widget=forms.Textarea(
            attrs={"rows": 3, "placeholder": "Explique o que mudou e por quê (obrigatório)."}),
    )

    # =================================================================
    # CAMPOS JUDICIAIS (espelhados do CreateForm)
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

    # Lista de campos que não podem ser alterados após a criação
    LOCKED_FIELDS = (
        "especialidade",
        "procedimento",
        "procedimento_secundario",
        "especialidade_secundario",
        "paciente",
        "medico",
    )

    class Meta:
        model = ListaEsperaCirurgica
        fields = [
            # FKs principais (serão travados)
            "especialidade",
            "procedimento",
            "procedimento_secundario",
            "especialidade_secundario",
            "paciente",
            "medico",
            
            # Campos editáveis
            "prioridade",
            "prioridade_justificativa",
            "medida_judicial",
            "situacao",
            "observacoes",
            "data_novo_contato",
            
            # Campos judiciais
            "judicial_numero",
            "judicial_descricao",
            "judicial_anexos",
            
            # Campo de auditoria
            "motivo_alteracao",
        ]
        widgets = {
            "medida_judicial": forms.CheckboxInput(attrs={"class": "h-4 w-4 text-indigo-600 border-gray-300 rounded", "id": "id_medida_judicial"}),
            "observacoes": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Observações…"}
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
            "prioridade_justificativa": "Campo obrigatório caso a prioridade não seja 'Sem Prioridade'",
            "medida_judicial": "Marque se há decisão judicial aplicável.",
            "situacao": "Estado atual do paciente na fila.",
            "observacoes": "Anotações internas/observações livres.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name in self.LOCKED_FIELDS:
            if name in self.fields:
                current_class = self.fields[name].widget.attrs.get("class", "")
                
                self.fields[name].widget.attrs.update(
                    {
                        "readonly": True, # Ajuda, embora <select> não o respeite
                        "class": (current_class + " bg-gray-50 cursor-not-allowed pointer-events-none appearance-none").strip(),
                        "title": "Campo bloqueado na edição",
                    }
                )
        
        # Define a ordem visual dos campos no formulário
        desired_order = [
            "especialidade",
            "procedimento",
            "procedimento_secundario",
            "especialidade_secundario",
            "medico",
            "paciente",
            "prioridade", "prioridade_justificativa", "medida_judicial",
            "judicial_numero", "judicial_descricao", "judicial_anexos",
            "situacao",
            "observacoes",
            "data_novo_contato",
            "motivo_alteracao"
        ]
        self.order_fields([f for f in desired_order if f in self.fields])

        # Permite que o campo de data aceite formatos comuns
        if "data_novo_contato" in self.fields:
            self.fields["data_novo_contato"].input_formats = ["%Y-%m-%d", "%d/%m/%Y"]

        # Oculta "motivo_alteracao" se o registro já estiver inativo (não faz sentido exigir)
        if self.instance and not self.instance.ativo and "motivo_alteracao" in self.fields:
            self.fields.pop("motivo_alteracao")

    def clean(self):
        cleaned = super().clean()
        
        # Validação extra para impedir mudanças nos campos travados (via POST injection)
        for name in self.LOCKED_FIELDS:
            if name in self.changed_data:
                self.add_error(name, "Este campo não pode ser alterado.")
                cleaned[name] = getattr(self.instance, name)

        # Validação da regra de negócio: prioridade não-padrão exige justificativa
        prioridade = (cleaned.get("prioridade") or "").strip()
        prioridade_justificativa = (cleaned.get("prioridade_justificativa") or "").strip()
        if prioridade != "SEM" and not prioridade_justificativa:
            self.add_error("prioridade_justificativa",
                           "Informe o motivo dessa prioridade.")
            
        return cleaned


class FilaCreateForm(forms.ModelForm):
    """
    Formulário para CRIAÇÃO de uma entrada da fila.
    - Usa campos `*_api` (ChoiceFields) que são populados via AJAX (Select2).
    - O método .save() resolve esses IDs em objetos reais do banco.
    """
    
    # =================================================================
    # CAMPOS DE BUSCA (Select2 + AJAX)
    #
    # O atributo 'data-autocomplete-url' é a "ponte" entre o Django e o
    # JavaScript. O Django renderiza a URL correta, e o JS a consome.
    # =================================================================
    
    especialidade_api = forms.ChoiceField(
        label="Especialidade",
        required=True,
        choices=[("", "Digite para buscar…")],
        widget=forms.Select(attrs={
            "id": "id_especialidade_api",
            "data-autocomplete-url": reverse_lazy("fila_cirurgica:especialidade_api_autocomplete")
        }),
    )
    procedimento_api = forms.ChoiceField(
        label="Procedimento",
        required=True,
        choices=[("", "Digite para buscar…")],
        widget=forms.Select(attrs={
            "id": "id_procedimento_api",
            "data-autocomplete-url": reverse_lazy("fila_cirurgica:procedimento_api_autocomplete")
        }),
    )
    especialidade_secundario_api = forms.ChoiceField(
        label="Especialidade Secundária",
        required=False,
        choices=[("", "Digite para buscar…")],
        widget=forms.Select(attrs={
            "id": "id_especialidade_secundario_api",
            "data-autocomplete-url": reverse_lazy("fila_cirurgica:especialidade_api_autocomplete")
        }),
    )
    procedimento_secundario_api = forms.ChoiceField(
        label="Procedimento Secundário",
        required=False,
        choices=[("", "Digite para buscar…")],
        widget=forms.Select(attrs={
            "id": "id_procedimento_secundario_api",
            "data-autocomplete-url": reverse_lazy("fila_cirurgica:procedimento_api_autocomplete")
        }),
    )
    medico_api = forms.ChoiceField(
        label="Médico",
        required=True,
        choices=[("", "Digite para buscar…")],
        widget=forms.Select(attrs={
            "id": "id_medico_api",
            "data-autocomplete-url": reverse_lazy("fila_cirurgica:medico_api_autocomplete")
        }),
    )
    prontuario = forms.ChoiceField(
        label="Prontuário",
        required=True,
        choices=[("", "Digite para buscar…")],
        widget=forms.Select(attrs={
            "id": "id_prontuario",
            "data-autocomplete-url": reverse_lazy("fila_cirurgica:paciente_api_autocomplete")
        }),
    )

    # =================================================================
    # CAMPOS JUDICIAIS
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
        label="Anexos do Processo",
        required=False,
        widget=forms.FileInput(attrs={"id": "id_judicial_anexos"})
    )

    class Meta:
        model = ListaEsperaCirurgica
        # Campos do modelo que serão renderizados diretamente
        fields = [
           # Campos editáveis
            "prioridade",
            "prioridade_justificativa",
            "medida_judicial",
            "situacao",
            "observacoes",
            "data_novo_contato",
            
            # Campos judiciais
            "judicial_numero",
            "judicial_descricao",
            "judicial_anexos",
        ]
        widgets = {
            "medida_judicial": forms.CheckboxInput(
                attrs={"class": "h-4 w-4 text-indigo-600 border-gray-300 rounded", "id": "id_medida_judicial"}
            ),
            "observacoes": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Observações…"}
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

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        def ensure_choice(field_name: str) -> None:
            """
            Garante que o valor enviado (via POST) em um Select2 AJAX
            seja adicionado aos 'choices' do campo. Isso é necessário
            para que o Django valide um valor que ele não conhece (pois
            foi carregado via API).
            """
            field = self.fields[field_name]
            # Pega o valor enviado (do POST ou 'initial')
            value = self.data.get(field_name) or self.initial.get(field_name)
            if not value:
                return
            
            # Pega o texto (label) do valor
            label = self.data.get(f"{field_name}_text") or str(value)
            
            # Adiciona (valor, label) aos choices se ainda não existir
            if not any(str(value) == str(v) for v, _ in field.choices):
                field.choices = list(field.choices) + [(str(value), label)]

        # Aplica a função 'ensure_choice' em todos os campos de Select2 AJAX
        for name in (
            "especialidade_api", "procedimento_api", 
            "especialidade_secundario_api", "procedimento_secundario_api",
            "medico_api", "prontuario"
        ):
            ensure_choice(name)

        # Define a ordem visual dos campos
        desired_order = [
            "especialidade_api",
            "procedimento_api",
            "especialidade_secundario_api",
            "procedimento_secundario_api",
            "medico_api",
            "prontuario",
            "prioridade",
            "prioridade_justificativa",
            "medida_judicial",
            "judicial_numero", 
            "judicial_descricao", 
            "judicial_anexos",
            "situacao",
            "observacoes", "data_novo_contato", 
        ]
        # Filtra 'desired_order' para conter apenas campos que existem neste form
        self.order_fields([f for f in desired_order if f in self.fields])

    def clean(self) -> dict:
        cleaned = super().clean()
        
        # Validação da regra de negócio: prioridade não-padrão exige justificativa
        prioridade = (cleaned.get("prioridade") or "").strip()
        prioridade_justificativa = (cleaned.get("prioridade_justificativa") or "").strip()
        if prioridade != "SEM" and not prioridade_justificativa:
            self.add_error("prioridade_justificativa",
                           "Informe o motivo dessa prioridade.")
        return cleaned

    def save(self, commit: bool = True) -> ListaEsperaCirurgica:
        """
        Sobrescreve o .save() para resolver os IDs dos campos `*_api`
        em objetos reais do banco, usando os `api_helpers`.
        """
        # Cria a instância do modelo, mas não salva no banco ainda
        instance: ListaEsperaCirurgica = super().save(commit=False)

        # 1. Coleta os IDs enviados pelos campos Select2
        prontuario = self.cleaned_data["prontuario"].strip()
        esp_id = str(self.cleaned_data["especialidade_api"])
        proc_id = str(self.cleaned_data["procedimento_api"])
        med_id = str(self.cleaned_data["medico_api"])
        proc_sec_id = self.cleaned_data.get("procedimento_secundario_api")
        esp_sec_id = self.cleaned_data.get("especialidade_secundario_api")

        # 2. Usa os 'helpers' para buscar ou criar os objetos FK
        # (Isso desacopla o form da lógica de API)
        instance.paciente = get_or_create_paciente(prontuario=prontuario)
        instance.especialidade = get_or_create_especialidade(esp_id)
        instance.procedimento = get_or_create_procedimento(proc_id)
        instance.medico = get_or_create_profissional(med_id)

        # 3. Processa os campos secundários (opcionais)
        if proc_sec_id and esp_sec_id:
            instance.procedimento_secundario = get_or_create_procedimento(proc_sec_id)
            instance.especialidade_secundario = get_or_create_especialidade(esp_sec_id)
        else:
            instance.procedimento_secundario = None
            instance.especialidade_secundario = None

        # 4. Salva a instância no banco (se commit=True)
        if commit:
            instance.save()
            
        return instance


class FilaDeactivateForm(forms.Form):
    """
    Formulário para "remoção" (inativação) de uma entrada.
    Pede um motivo estruturado (choices) e uma justificativa textual.
    """
    motivo = forms.ChoiceField(
        label="Motivo da remoção",
        choices=(),  # Preenchido dinamicamente no __init__
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
        
        # Carrega dinamicamente os 'choices' do modelo.
        # Isso garante que o form esteja sempre em sincronia com o models.py.
        try:
            field = ListaEsperaCirurgica._meta.get_field("motivo_saida")
            if getattr(field, "choices", None):
                self.fields["motivo"].choices = list(field.choices)
        except Exception:
            # Em caso de falha, o campo 'motivo' ficará sem opções
            pass
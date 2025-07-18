from django import forms
from .models import ListaEsperaCirurgica, ProcedimentoAghu, PacienteAghu, ProfissionalAghu, EspecialidadeAghu
from django.urls import reverse_lazy

class PacienteForm(forms.ModelForm):
    class Meta:
        model = PacienteAghu
        fields = [
            'prontuario',
        ]

    def clean_telefone_contato_principal(self):
        telefone = self.cleaned_data.get('telefone_contato_principal')
        if telefone and not telefone.isdigit():
            raise forms.ValidationError('Preencha o telefone apenas com números.')
        return telefone

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['telefone_contato_principal', 'telefone_contato_secundario']:
            widget = self.fields[field].widget
            widget.attrs.update({
                'placeholder': 'Ex.: XX X XXXX - XXXX',
                'class': widget.attrs.get('class', '') + ' mask-telefone'
            })


class ListaEsperaCirurgicaForm(forms.ModelForm):

    class RawChoiceField(forms.ChoiceField):
        def validate(self, value):
            if self.required and not value:
                raise forms.ValidationError(self.error_messages['required'], code='required')

    # --- Campo "Fake" para Procedimento ---
    procedimento_api_choice = RawChoiceField(
        label='Procedimento', required=True, widget=forms.Select(attrs={
            'class': 'admin-autocomplete',
            'data-ajax-url': reverse_lazy('fila_cirurgica:procedimento_api_autocomplete'),
            'data-theme': 'admin-autocomplete', 'data-allow-clear': 'false',
            'data-placeholder': 'Busque o procedimento',
        }),
        help_text="Selecione a especialidade antes de selecionar o procedimento."
    )
    # --- Campo "Fake" para Paciente ---
    paciente_api_choice = RawChoiceField(
        label='Paciente', required=True, widget=forms.Select(attrs={
            'class': 'admin-autocomplete',
            'data-ajax-url': reverse_lazy('fila_cirurgica:paciente_api_autocomplete'),
            'data-theme': 'admin-autocomplete', 'data-allow-clear': 'false',
            'data-placeholder': 'Busque o paciente por nome ou prontuário',
        })
    )
    # --- Campo "Fake" para Médico ---
    medico_api_choice = RawChoiceField(
        label='Médico', required=False, widget=forms.Select(attrs={
            'class': 'admin-autocomplete',
            'data-ajax-url': reverse_lazy('fila_cirurgica:medico_api_autocomplete'),
            'data-theme': 'admin-autocomplete', 'data-allow-clear': 'true', # Allow-clear para campos opcionais
            'data-placeholder': 'Busque o médico por nome ou matrícula',
        })
    )
    # --- Campo "Fake" para Especialidade ---
    especialidade_api_choice = RawChoiceField(
        label='Especialidade', required=True, widget=forms.Select(attrs={
            'class': 'admin-autocomplete',
            'data-ajax-url': reverse_lazy('fila_cirurgica:especialidade_api_autocomplete'),
            'data-theme': 'admin-autocomplete', 'data-allow-clear': 'false',
            'data-placeholder': 'Busque a especialidade',
        })
    )
    
    change_reason = forms.CharField(
        label="Motivo da alteração",
        max_length=100,
        required=True,
    )

    class Meta:
        model = ListaEsperaCirurgica
        exclude = ('procedimento', 'paciente', 'medico', 'especialidade')
        fields = [
            'especialidade_api_choice',
            'procedimento_api_choice',
            'paciente_api_choice',
            'medico_api_choice',
            'prioridade',
            'medida_judicial',
            'situacao',
            'observacoes',
            'data_novo_contato',
            'change_reason'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pré-popula os campos se estivermos editando um registro existente
        if self.instance and self.instance.pk:
            if self.instance.procedimento:
                proc = self.instance.procedimento
                self.fields['procedimento_api_choice'].choices = [(proc.codigo, f"{proc.codigo} - {proc.nome}")]
            if self.instance.paciente:
                pac = self.instance.paciente
                self.fields['paciente_api_choice'].choices = [(pac.prontuario, f"{pac.nome} (Prontuário: {pac.prontuario}")]
            if self.instance.medico:
                med = self.instance.medico
                self.fields['medico_api_choice'].choices = [(med.matricula, f"{med.nome} (Matrícula: {med.matricula}")]
            if self.instance.especialidade:
                esp = self.instance.especialidade
                self.fields['especialidade_api_choice'].choices = [(esp.cod_especialidade, esp.nome_especialidade)]

    def clean_procedimento_api_choice(self):
        data = self.cleaned_data.get('procedimento_api_choice')
        if not data:
            raise forms.ValidationError("Este campo é obrigatório.")
        return data

    def clean_paciente_api_choice(self):
        data = self.cleaned_data.get('paciente_api_choice')
        if not data:
            raise forms.ValidationError("Este campo é obrigatório.")
        return data

    def clean_especialidade_api_choice(self):
        data = self.cleaned_data.get('especialidade_api_choice')
        if not data:
            raise forms.ValidationError("Este campo é obrigatório.")
        return data

    def clean_medico_api_choice(self):
        data = self.cleaned_data.get('medico_api_choice')
        if not data:
            raise forms.ValidationError("Este campo é obrigatório.")
        return data

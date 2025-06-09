# forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import Paciente, ListaEsperaCirurgica, EspecialidadeProcedimento

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = [
            'nome', 'data_nascimento', 'sexo',
            'telefone_contato_principal', 'telefone_contato_secundario',
            'nome_responsavel', 'numero_prontuario'
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

import unfold.widgets

class ListaEsperaCirurgicaForm(forms.ModelForm):
    class Meta:
        model = ListaEsperaCirurgica
        fields = [
            'especialidade','procedimento', 'paciente',
            'prioridade', 'medida_judicial', 'medico',
            'situacao', 'observacoes', 'data_novo_contato',
            'change_reason'
        ]
        
    change_reason = forms.CharField(
        label="Motivo da alteração",
        max_length=100,
        required=True,
    )

    def clean(self):
        cleaned = super().clean()
        proc = cleaned.get('procedimento')
        esp = cleaned.get('especialidade')
        if proc and esp:
            if not EspecialidadeProcedimento.objects.filter(
                procedimento=proc,
                especialidade=esp
            ).exists():
                raise ValidationError('Especialidade e procedimento incompatíveis.')
        return cleaned

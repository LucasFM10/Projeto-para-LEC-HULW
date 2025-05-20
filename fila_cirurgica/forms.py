# forms.py
from django import forms
from .models import Paciente, ListaEsperaCirurgica


class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = [
            'nome', 'data_nascimento', 'sexo', 'telefone_contato_principal',
            'telefone_contato_secundario', 'nome_responsavel', 'numero_prontuario'
        ]

    def clean_telefone_contato_principal(self):
        telefone = self.cleaned_data.get('telefone_contato_principal')
        if telefone and not telefone.isdigit():
            raise forms.ValidationError('Preencha o telefone para contato apenas com números.')
        return telefone

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in [
            'telefone_contato_principal', 'telefone_contato_secundario'
        ]:
            widget = self.fields[field].widget
            widget.attrs.update({
                'placeholder': 'Ex.: XX X XXXX - XXXX',
                'class': widget.attrs.get('class', '') + ' mask-telefone'
            })


class ListaEsperaCirurgicaForm(forms.ModelForm):
    class Meta:
        model = ListaEsperaCirurgica
        fields = [
            'procedimento', 'paciente', 'prioridade', 'medida_judicial',
            'medico', 'situacao', 'observacoes', 'data_novo_contato'
        ]
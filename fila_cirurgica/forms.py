from django import forms
from django.core.exceptions import ValidationError
from django.forms import TextInput

from .models import Paciente

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = [
                'nome',
                'data_nascimento',
                'sexo',
                'telefone_contato_principal',
                'telefone_contato_secundario',
                'nome_responsavel',
                'numero_prontuario'
            ]
    
    def clean_telefone_contato_principal(self):
        telefone = self.cleaned_data.get('telefone_contato_principal')
        if telefone and not telefone.isdigit():
            raise ValidationError('Preencha o telefone para contato apenas com números.')
        return telefone
    

    def __init__(self, *args, **kwargs):
        super(PacienteForm, self).__init__(*args, **kwargs)
        widget_telefone_principal = self.fields["telefone_contato_principal"].widget
        widget_telefone_principal.attrs['placeholder'] = 'Ex.: XX X XXXX - XXXX'
        widget_telefone_principal.attrs['class'] = widget_telefone_principal.attrs.get('class') + ' mask-telefone'

        widget_telefone_contato_secundario = self.fields["telefone_contato_secundario"].widget
        widget_telefone_contato_secundario.attrs['placeholder'] = 'Ex.: XX X XXXX - XXXX'
        widget_telefone_contato_secundario.attrs['class'] = widget_telefone_contato_secundario.attrs.get('class') + ' mask-telefone'

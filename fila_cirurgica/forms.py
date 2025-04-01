from .models import Especialidade, ListaEsperaCirurgica
from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import AutocompleteSelect
from .models import Paciente, Especialidade, ListaEsperaCirurgica, EspecialidadeProcedimento


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
            raise forms.ValidationError(
                'Preencha o telefone para contato apenas com números.')
        return telefone

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ["telefone_contato_principal", "telefone_contato_secundario"]:
            widget = self.fields[field].widget
            widget.attrs.update({
                'placeholder': 'Ex.: XX X XXXX - XXXX',
                'class': widget.attrs.get('class', '') + ' mask-telefone'
            })


class FakeRelation:
    """Engana o Django para que `AutocompleteSelect` funcione em campos que não são ForeignKey."""

    def __init__(self, model, field_name):
        self.model = model
        self.name = field_name
        self.remote_field = self  # Adiciona `remote_field` para evitar erro


class CustomAutocompleteSelect(AutocompleteSelect):
    """Usa `FakeRelation` para permitir `AutocompleteSelect` no formulário personalizado."""

    def __init__(self, model, field_name, admin_site, attrs=None, choices=(), using=None):
        rel = FakeRelation(model, field_name)
        super().__init__(rel, admin_site, attrs=attrs, choices=choices, using=using)


class ListaEsperaCirurgicaForm(forms.ModelForm):
    especialidade = forms.ModelChoiceField(
        queryset=Especialidade.objects.all(),
        required=False,
        label="Especialidade",
        widget=CustomAutocompleteSelect(
            EspecialidadeProcedimento, "especialidade", admin.site, attrs={'disabled': 'disabled'}),
    )

    class Meta:
        model = ListaEsperaCirurgica
        fields = ['especialidade', 'procedimento', 'paciente', 'paciente_oncologico', 'urgencia', 'medida_judicial',
                  'medico', 'situacao', 'observacoes', 'data_novo_contato']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.procedimento:
            especialidade_procedimento = EspecialidadeProcedimento.objects.filter(
                procedimento=self.instance.procedimento).first()
            if especialidade_procedimento:
                self.fields['especialidade'].initial = especialidade_procedimento.especialidade

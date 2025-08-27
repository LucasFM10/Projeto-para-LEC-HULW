import django_filters
from django import forms
from fila_cirurgica.models import ListaEsperaCirurgica


class FilaFilter(django_filters.FilterSet):
    # Texto (icontains) nas relações
    especialidade = django_filters.CharFilter(field_name="especialidade__nome_especialidade", lookup_expr="icontains", label="Especialidade")
    procedimento  = django_filters.CharFilter(field_name="procedimento__nome", lookup_expr="icontains", label="Procedimento")
    medico        = django_filters.CharFilter(field_name="medico__nome", lookup_expr="icontains", label="Médico")

    # Campos diretos
    prioridade    = django_filters.CharFilter(field_name="prioridade", lookup_expr="exact", label="Prioridade")
    ativo         = django_filters.BooleanFilter(field_name="ativo", label="Ativo")
    medida_judicial = django_filters.BooleanFilter(field_name="medida_judicial", label="Medida Judicial")

    # Intervalo de datas (data/hora de entrada na fila)
    data_entrada = django_filters.DateFromToRangeFilter(
        field_name="data_entrada",
        label="Data de Entrada (de/até)",
        widget=django_filters.widgets.RangeWidget(
            attrs={"type": "date", "class": "border rounded px-3 py-2"}
        ),
    )

    # Prontuário (exato)
    prontuario = django_filters.CharFilter(field_name="paciente__prontuario", lookup_expr="exact", label="Prontuário")

    class Meta:
        model = ListaEsperaCirurgica
        fields = ["especialidade", "procedimento", "medico", "prioridade", "ativo", "medida_judicial", "data_entrada", "prontuario"]

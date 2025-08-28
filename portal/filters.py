# portal/filters.py
from __future__ import annotations

import django_filters as df
from django import forms
from fila_cirurgica.models import (
    ListaEsperaCirurgica,
    EspecialidadeAghu as Especialidade,
    ProcedimentoAghu as Procedimento,
    ProfissionalAghu as Profissional,
)


class _TriStateChoiceFilter(df.ChoiceFilter):
    """
    Tri-state: '', '1', '0' -> Todos, Sim, Não
    Útil para BooleanFields quando queremos a opção 'Todos'.
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            "choices",
            (
                ("", "Todos"),
                ("1", "Sim"),
                ("0", "Não"),
            ),
        )
        # Mantém rótulo/placeholder simpáticos no template
        kwargs.setdefault("empty_label", "Todos")
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        if value == "1":
            return qs.filter(**{self.field_name: True})
        if value == "0":
            return qs.filter(**{self.field_name: False})
        return qs  # '' -> sem filtro


class FilaFilter(df.FilterSet):
    """
    - Especialidade, Procedimento, Médico: múltiplos, baseados em códigos externos
      via Select2 + API, mapeando por `to_field_name`.
    - Datas: filtros min/max.
    - Booleanos: tri-state (Todos / Sim / Não).
    - Prontuário: busca parcial (icontains).
    """

    # ----- Seletores múltiplos (por código externo) -----
    # Observação: `to_field_name` garante que os valores enviados pelo Select2 (id externo)
    # são traduzidos para o FK certo, sem exigir PK interno.
    especialidade = df.ModelMultipleChoiceFilter(
        label="Especialidade",
        field_name="especialidade__cod_especialidade",
        queryset=Especialidade.objects.order_by("nome_especialidade"),
        to_field_name="cod_especialidade",
        widget=forms.SelectMultiple(attrs={"id": "id_especialidade"}),
    )

    procedimento = df.ModelMultipleChoiceFilter(
        label="Procedimento",
        field_name="procedimento__codigo",
        queryset=Procedimento.objects.order_by("nome"),
        to_field_name="codigo",
        widget=forms.SelectMultiple(attrs={"id": "id_procedimento"}),
    )

    medico = df.ModelMultipleChoiceFilter(
        label="Médico",
        field_name="medico__matricula",
        queryset=Profissional.objects.order_by("nome"),
        to_field_name="matricula",
        widget=forms.SelectMultiple(attrs={"id": "id_medico"}),
    )

    # ----- Outros filtros -----
    prioridade = df.ChoiceFilter(
        label="Prioridade",
        field_name="prioridade",
        choices=getattr(ListaEsperaCirurgica, "PRIORIDADE_CHOICES", ()),
        empty_label="Todas",
        widget=forms.Select(attrs={"id": "id_prioridade"}),
    )

    ativo = _TriStateChoiceFilter(
        label="Ativo",
        field_name="ativo",
        widget=forms.Select(attrs={"id": "id_ativo"}),
    )

    medida_judicial = _TriStateChoiceFilter(
        label="Medida Judicial",
        field_name="medida_judicial",
        widget=forms.Select(attrs={"id": "id_medida_judicial"}),
    )

    # Datas (de/até): mantém a query antiga data_entrada_min / data_entrada_max
    data_entrada_min = df.DateFilter(
        label="Data de Entrada (de)",
        field_name="data_entrada",
        lookup_expr="gte",
        widget=forms.DateInput(attrs={"type": "date", "id": "id_data_entrada_min"}),
    )
    data_entrada_max = df.DateFilter(
        label="Data de Entrada (até)",
        field_name="data_entrada",
        lookup_expr="lte",
        widget=forms.DateInput(attrs={"type": "date", "id": "id_data_entrada_max"}),
    )

    prontuario = df.CharFilter(
        label="Prontuário",
        field_name="paciente__prontuario",
        lookup_expr="icontains",
        widget=forms.TextInput(attrs={"placeholder": "Ex.: 12345", "id": "id_prontuario"}),
    )

    class Meta:
        model = ListaEsperaCirurgica
        fields = [
            "especialidade",
            "procedimento",
            "medico",
            "prioridade",
            "ativo",
            "medida_judicial",
            "data_entrada_min",
            "data_entrada_max",
            "prontuario",
        ]

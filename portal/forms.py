# portal/forms.py
from django import forms
from django.conf import settings            # <-- novo
import requests                              # <-- novo
from fila_cirurgica.models import ListaEsperaCirurgica

class PortalCreateFormLight(forms.ModelForm):
    # ---- CAMPO NOVO (fake, só para exibir opções vindas da API) ----
    especialidade_api = forms.ChoiceField(
        label="Especialidade",
        required=True,
        choices=[("", "Digite para buscar…")],
        widget=forms.Select(attrs={"id": "id_especialidade_api"})
    )

    class Meta:
        model = ListaEsperaCirurgica
        fields = ["prioridade", "medida_judicial", "situacao", "observacoes"]
        widgets = {
            "medida_judicial": forms.CheckboxInput(attrs={"class": "h-4 w-4"}),
            "observacoes": forms.Textarea(attrs={
                "rows": 4, "placeholder": "Observações gerais…",
                "class": "w-full border rounded px-3 py-2",
            }),
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

        # Estiliza inputs padrão (Select/Char/etc.) com classes Tailwind
        for name, field in self.fields.items():
            if name in {"medida_judicial", "observacoes"}:
                continue
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (css + " w-full border rounded px-3 py-2").strip()

        # Padrão visual
        if "medida_judicial" in self.fields and (self.initial.get("medida_judicial") is None):
            self.initial["medida_judicial"] = False

        # ---- POPULAR CHOICES DA ESPECIALIDADE PELA API ----
        self.fields["especialidade_api"].choices = self._carregar_choices_especialidades()

    # ---------------- helpers ----------------

    def _carregar_choices_especialidades(self):
        """
        Busca especialidades na API e retorna como lista de (id, nome).
        Tenta entender formatos comuns:
          - lista simples: [{"COD_ESPECIALIDADE": ..., "NOME_ESPECIALIDADE": ...}, ...]
          - paginado: {"results": [...]}
          - nomes alternativos: {"id": ..., "nome": ...}
        Se a API falhar, devolve uma opção de fallback.
        """
        base = getattr(settings, "API_BASE_URL", "").rstrip("/")
        if not base:
            return [("", "API_BASE_URL não configurada")]

        url = f"{base}/especialidades"
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            data = resp.json()

            items = data.get("results", data) if isinstance(data, dict) else data
            choices = [("", "Selecione...")]

            for it in items:
                # tenta vários nomes de campos
                cod = (it.get("COD_ESPECIALIDADE")
                       or it.get("cod_especialidade")
                       or it.get("id")
                       or it.get("codigo"))
                nome = (it.get("NOME_ESPECIALIDADE")
                        or it.get("nome_especialidade")
                        or it.get("nome")
                        or it.get("descricao"))

                if cod is not None and nome:
                    choices.append((str(cod), str(nome)))

            if len(choices) == 1:
                # nada compreensível
                return [("", "Nenhuma especialidade disponível")]

            return choices

        except requests.RequestException as e:
            # Log leve (você pode usar logging)
            print(f"[PortalCreateFormLight] Falha ao buscar especialidades: {e}")
            return [("", "Falha ao carregar especialidades")]
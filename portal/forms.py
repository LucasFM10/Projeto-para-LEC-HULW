from django import forms
from fila_cirurgica.models import ListaEsperaCirurgica

# Tenta reaproveitar o ModelForm oficial do projeto (se existir)
try:
    from fila_cirurgica.forms import ListaEsperaCirurgicaForm as BaseListaEsperaForm
except Exception:
    class BaseListaEsperaForm(forms.ModelForm):
        """Fallback simples, mantendo compatibilidade básica."""
        class Meta:
            model = ListaEsperaCirurgica
            fields = "__all__"
            widgets = {
                # Exemplos de widgets com Tailwind (ajuste nomes conforme seus campos)
                # "prioridade": forms.NumberInput(attrs={"class": "w-full border rounded px-3 py-2"}),
                # "medida_judicial": forms.CheckboxInput(attrs={"class": "h-4 w-4"}),
            }


class PortalListaEsperaForm(BaseListaEsperaForm):
    """Form usado no Portal. Se o registro estiver inativo, torna-se somente leitura."""
    change_reason = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "w-full border rounded px-3 py-2"}),
        help_text="Motivo da alteração (opcional).",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Aplica classes Tailwind nos widgets que ainda não têm
        for name, field in self.fields.items():
            w = field.widget
            if not getattr(w.attrs, "get", None):
                continue
            css = w.attrs.get("class", "")
            if isinstance(w, (forms.TextInput, forms.Textarea, forms.NumberInput, forms.Select, forms.DateInput, forms.DateTimeInput)):
                w.attrs["class"] = (css + " w-full border rounded px-3 py-2").strip()
            elif isinstance(w, (forms.CheckboxInput,)):
                w.attrs["class"] = (css + " h-4 w-4").strip()

        # Se for instância e estiver inativa, desabilita todos os campos
        inst = getattr(self, "instance", None)
        if inst and hasattr(inst, "ativo") and inst.ativo is False:
            for f in self.fields.values():
                f.disabled = True

    class Meta(BaseListaEsperaForm.Meta):
        # herda Meta, mas garante que widgets/tailwind sejam mantidos quando necessário
        pass

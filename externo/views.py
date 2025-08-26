from django.shortcuts import render
from fila_cirurgica.models import ListaEsperaCirurgica

def consulta_posicao(request):
    posicao = None
    mensagem = None

    if request.method == "POST":
        prontuario = request.POST.get("prontuario", "").strip()

        if prontuario:
            entrada = ListaEsperaCirurgica.objects.filter(
                paciente__prontuario=prontuario,
                ativo=True
            ).first()

            if entrada:
                posicao = entrada.get_posicao()
            else:
                mensagem = "❌ Prontuário inválido ou paciente não está na fila."
        else:
            mensagem = "⚠️ Por favor, digite um número de prontuário."

    return render(request, "externo/consulta_posicao.html", {
        "posicao": posicao,
        "mensagem": mensagem
    })

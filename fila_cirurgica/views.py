from django.http import JsonResponse
from .models import EspecialidadeProcedimento

def get_especialidade(request, procedimento_id):
    try:
        especialidade_procedimento = EspecialidadeProcedimento.objects.filter(procedimento_id=procedimento_id).first()
        especialidade = especialidade_procedimento.especialidade if especialidade_procedimento else None
        if especialidade:
            especialidade_id =especialidade.id
            especialidade_nome = especialidade.nome_especialidade
            return JsonResponse({"especialidade_id": especialidade_id, "especialidade_nome": especialidade_nome}, safe=False)
        else:
            return JsonResponse({"especialidade_id": None, "especialidade_nome": None}, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500, content_type="application/json")

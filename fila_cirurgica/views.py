import requests
from django.http import JsonResponse

API_BASE_URL = "http://127.0.0.1:8000/api/v1"

def _api_autocomplete_proxy(request, api_endpoint, id_field, text_format_str):
    """Função auxiliar genérica para evitar repetição de código."""
    term = request.GET.get('term', '')
    page = request.GET.get('page')
    params = {'term': term, 'limit': 25}
    if page:
        params['page'] = page

    try:
        response = requests.get(f"{API_BASE_URL}/{api_endpoint}/", params=params)
        response.raise_for_status()
        api_data = response.json()
        
        results = [
            {"id": item[id_field], "text": text_format_str.format(**item)}
            for item in api_data
        ]
        more = len(results) == params.get('limit', 25)
        return JsonResponse({"results": results, "pagination": {"more": more}})
    except requests.RequestException:
        return JsonResponse({'error': 'Falha ao contatar a API'}, status=500)

# View para Procedimento (já existente)
def procedimento_api_autocomplete(request):
    return _api_autocomplete_proxy(
        request,
        api_endpoint='procedimentos',
        id_field='COD_PROCEDIMENTO',
        text_format_str='{COD_PROCEDIMENTO} - {PROCEDIMENTO}'
    )

# NOVA VIEW para Paciente
def paciente_api_autocomplete(request):
    return _api_autocomplete_proxy(
        request,
        api_endpoint='pacientes',
        id_field='PRONTUARIO_PAC',
        text_format_str='{NOME_PACIENTE} (Prontuário: {PRONTUARIO_PAC})'
    )

# NOVA VIEW para Médico/Profissional
def medico_api_autocomplete(request):
    return _api_autocomplete_proxy(
        request,
        api_endpoint='profissionais',
        id_field='MATRICULA',
        text_format_str='{NOME_PROFISSIONAL} (Matrícula: {MATRICULA})'
    )

# NOVA VIEW para Especialidade
def especialidade_api_autocomplete(request):
    return _api_autocomplete_proxy(
        request,
        api_endpoint='especialidades',
        id_field='COD_ESPECIALIDADE',
        text_format_str='{NOME_ESPECIALIDADE}'
    )
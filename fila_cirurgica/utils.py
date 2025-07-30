# fila_cirurgica/utils.py
import requests
from django.http import JsonResponse
from django.conf import settings

def api_autocomplete_proxy(request, api_endpoint, id_field, text_format_str):
    term = request.GET.get('term', '')
    page = request.GET.get('page')
    params = {'term': term, 'limit': 25}
    if page:
        params['page'] = page

    try:
        response = requests.get(f"{settings.API_BASE_URL}/{api_endpoint}/", params=params)
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

# fila_cirurgica/api_helpers.py

import requests
from django.conf import settings
from .models import (
    PacienteAghu,
    ProcedimentoAghu,
    EspecialidadeAghu,
    ProfissionalAghu,
)

def get_or_create_paciente(prontuario):
    if not prontuario:
        return None

    response = requests.get(f"{settings.API_BASE_URL}/pacientes/{prontuario}")
    response.raise_for_status()
    data = response.json()

    obj, created = PacienteAghu.objects.get_or_create(
        prontuario=data['PRONTUARIO_PAC'],
        defaults={'nome': data['NOME_PACIENTE']}
    )
    if not created and obj.nome != data['NOME_PACIENTE']:
        obj.nome = data['NOME_PACIENTE']
        obj.save()
    return obj

def get_or_create_procedimento(codigo):
    if not codigo:
        return None

    response = requests.get(f"{settings.API_BASE_URL}/procedimentos/{codigo}")
    response.raise_for_status()
    data = response.json()

    obj, created = ProcedimentoAghu.objects.get_or_create(
        codigo=data['COD_PROCEDIMENTO'],
        defaults={'nome': data['PROCEDIMENTO']}
    )
    if not created and obj.nome != data['PROCEDIMENTO']:
        obj.nome = data['PROCEDIMENTO']
        obj.save()
    return obj

def get_or_create_especialidade(cod_especialidade):
    if not cod_especialidade:
        return None

    response = requests.get(f"{settings.API_BASE_URL}/especialidades/{cod_especialidade}")
    response.raise_for_status()
    data = response.json()

    obj, created = EspecialidadeAghu.objects.get_or_create(
        cod_especialidade=data['COD_ESPECIALIDADE'],
        defaults={'nome_especialidade': data['NOME_ESPECIALIDADE']}
    )
    if not created and obj.nome_especialidade != data['NOME_ESPECIALIDADE']:
        obj.nome_especialidade = data['NOME_ESPECIALIDADE']
        obj.save()
    return obj

def get_or_create_profissional(matricula):
    if not matricula:
        return None

    response = requests.get(f"{settings.API_BASE_URL}/profissionais/{matricula}")
    response.raise_for_status()
    data = response.json()

    obj, created = ProfissionalAghu.objects.get_or_create(
        matricula=data['MATRICULA'],
        defaults={'nome': data['NOME_PROFISSIONAL']}
    )
    if not created and obj.nome != data['NOME_PROFISSIONAL']:
        obj.nome = data['NOME_PROFISSIONAL']
        obj.save()
    return obj

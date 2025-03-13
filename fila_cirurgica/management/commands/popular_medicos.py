from django.core.management.base import BaseCommand
from fila_cirurgica.models import Medico, Especialidade
import random

class Command(BaseCommand):
    help = "Popula o banco de dados com 40 médicos aleatórios e especialidades."

    def handle(self, *args, **kwargs):
        especialidades_disponiveis = list(Especialidade.objects.values_list("nome_especialidade", flat=True))

        medicos_data = [
            ("Dr. João Silva", "M001"),
            ("Dra. Maria Oliveira", "M002"),
            ("Dr. Carlos Souza", "M003"),
            ("Dra. Ana Costa", "M004"),
            ("Dr. Pedro Lima", "M005"),
            ("Dra. Fernanda Almeida", "M006"),
            ("Dr. Ricardo Gomes", "M007"),
            ("Dra. Beatriz Rocha", "M008"),
            ("Dr. Alexandre Mendes", "M009"),
            ("Dra. Camila Ferreira", "M010"),
            ("Dr. Gustavo Nunes", "M011"),
            ("Dra. Patrícia Duarte", "M012"),
            ("Dr. Leonardo Martins", "M013"),
            ("Dra. Luana Santos", "M014"),
            ("Dr. Rafael Barbosa", "M015"),
            ("Dra. Mariana Figueiredo", "M016"),
            ("Dr. Eduardo Campos", "M017"),
            ("Dra. Renata Moreira", "M018"),
            ("Dr. Henrique Vasconcelos", "M019"),
            ("Dra. Carolina Ribeiro", "M020"),
            ("Dr. Matheus Borges", "M021"),
            ("Dra. Aline Teixeira", "M022"),
            ("Dr. Felipe Costa", "M023"),
            ("Dra. Bianca Souza", "M024"),
            ("Dr. André Mendes", "M025"),
            ("Dra. Vanessa Castro", "M026"),
            ("Dr. Jorge Oliveira", "M027"),
            ("Dra. Larissa Lopes", "M028"),
            ("Dr. Thiago Fonseca", "M029"),
            ("Dra. Isabela Martins", "M030"),
            ("Dr. Daniel Ferreira", "M031"),
            ("Dra. Cláudia Lima", "M032"),
            ("Dr. Gabriel Monteiro", "M033"),
            ("Dra. Thaís Andrade", "M034"),
            ("Dr. Vinícius Campos", "M035"),
            ("Dra. Juliana Nogueira", "M036"),
            ("Dr. Otávio Correia", "M037"),
            ("Dra. Letícia Vieira", "M038"),
            ("Dr. Adriano Silveira", "M039"),
            ("Dra. Rafaela Mendes", "M040"),
        ]

        for i, (nome, matricula) in enumerate(medicos_data):
            medico, created = Medico.objects.get_or_create(matricula=matricula, nome=nome)
            
            # Escolhe aleatoriamente de 1 a 3 especialidades para cada médico
            num_especialidades = random.randint(1, 3)
            especialidades_nomes = random.sample(especialidades_disponiveis, min(num_especialidades, len(especialidades_disponiveis)))
            especialidades = Especialidade.objects.filter(nome_especialidade__in=especialidades_nomes).all()
            
            medico.especialidades.set(especialidades)

            self.stdout.write(f"{'Criado' if created else 'Já existe'}: {nome} - Matrícula: {matricula} - Especialidades: {', '.join(especialidades_nomes)}")

        self.stdout.write(self.style.SUCCESS("40 médicos cadastrados com sucesso!"))

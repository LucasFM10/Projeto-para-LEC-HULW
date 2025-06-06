# Generated by Django 5.1.3 on 2024-12-11 01:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fila_cirurgica', '0005_paciente_numero_prontuario_delete_prontuario'),
    ]

    operations = [
        migrations.CreateModel(
            name='ListaEsperaCirurgica',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_entrada', models.DateTimeField(auto_now_add=True)),
                ('prioridade', models.CharField(choices=[('P0', 'ONCOLOGIA'), ('P1', 'PACIENTES COM ALTA PRIORIDADE'), ('SP', 'SEM PRIORIDADE')])),
                ('demanda_judicial', models.BooleanField(null=True, verbose_name='Demanda Judicial')),
                ('situacao', models.CharField(choices=[('CA', 'CONSULTA AGENDADA'), ('AE', 'AGUARDANDO EXAMES'), ('DP', 'DOCUMENTAÇÃO PENDENTE'), ('EA', 'EXAMES EM ATRASO'), ('PP', 'PACIENTE PRONTO PARA CIRURGIA'), ('CA', 'CIRURGIA AGENDADA')])),
                ('observacoes', models.CharField(blank=True, max_length=255, null=True, verbose_name='observações')),
                ('data_novo_contato', models.DateField(verbose_name='Data para novo contato')),
                ('paciente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fila_cirurgica.paciente')),
                ('procedimentos', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fila_cirurgica.procedimento')),
            ],
        ),
    ]

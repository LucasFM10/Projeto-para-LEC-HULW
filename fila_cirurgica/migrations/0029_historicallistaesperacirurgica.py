# Generated by Django 5.1.3 on 2025-03-19 21:08

import django.db.models.deletion
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fila_cirurgica', '0028_alter_listaesperacirurgica_situacao_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalListaEsperaCirurgica',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('data_entrada', models.DateTimeField(blank=True, editable=False)),
                ('situacao', models.CharField(choices=[('CA', 'CONSULTA AGENDADA'), ('AE', 'EXAMES PENDENTES'), ('DP', 'DOCUMENTAÇÃO PENDENTE'), ('PP', 'PACIENTE PRONTO PARA CIRURGIA'), ('CNR', 'CONTATO NÃO REALIZADO'), ('T1F', 'TENTATIVA 1 FALHOU'), ('T2F', 'TENTATIVA 2 FALHOU'), ('T3F', 'TENTATIVA 3 FALHOU, NÃO SERÃO REALIZADOS NOVOS CONTATOS'), ('CRS', 'CONTATO REALIZADO COM SUCESSO')], verbose_name='Situação')),
                ('observacoes', models.CharField(blank=True, max_length=255, null=True, verbose_name='observações')),
                ('data_novo_contato', models.DateField(blank=True, null=True, verbose_name='Data para novo contato')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('medico', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='fila_cirurgica.medico')),
                ('paciente', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='fila_cirurgica.paciente')),
                ('procedimento', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='fila_cirurgica.procedimentoaghu')),
            ],
            options={
                'verbose_name': 'historical Lista de Espera Cirúrgica',
                'verbose_name_plural': 'historical Lista de Espera Cirúrgica',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]

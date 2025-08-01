# Generated by Django 5.2.1 on 2025-07-29 20:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fila_cirurgica', '0002_alter_historicalindicadorespecialidade_history_change_reason_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='historicallistaesperacirurgica',
            options={'get_latest_by': ('history_date', 'history_id'), 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical Lista de Espera Cirúrgica', 'verbose_name_plural': 'historical Lista de Espera Cirúrgica'},
        ),
        migrations.AlterField(
            model_name='historicallistaesperacirurgica',
            name='history_change_reason',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.DeleteModel(
            name='HistoricalIndicadorEspecialidade',
        ),
    ]

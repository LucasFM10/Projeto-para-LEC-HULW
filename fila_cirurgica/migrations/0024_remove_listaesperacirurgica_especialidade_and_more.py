# Generated by Django 5.1.3 on 2025-03-12 01:10

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fila_cirurgica', '0023_especialidadeprocedimento'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='listaesperacirurgica',
            name='especialidade',
        ),
        migrations.RemoveField(
            model_name='listaesperacirurgica',
            name='procedimento',
        ),
        migrations.AddField(
            model_name='listaesperacirurgica',
            name='especialidadeprocedimento',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='fila_cirurgica.especialidadeprocedimento'),
        ),
    ]

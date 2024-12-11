# Generated by Django 5.1.3 on 2024-12-11 00:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fila_cirurgica', '0004_prontuario_data_entrada_prontuario_numero_prontuario_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='paciente',
            name='numero_prontuario',
            field=models.CharField(default=1, max_length=20, verbose_name='Número do prontuário'),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='Prontuario',
        ),
    ]
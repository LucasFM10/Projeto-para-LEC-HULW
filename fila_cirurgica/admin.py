from django.utils.html import format_html
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group

from django.contrib import admin
from .models import Paciente, Procedimento, ListaEsperaCirurgica

from unfold.admin import ModelAdmin, TabularInline

admin.site.unregister(User)
admin.site.unregister(Group)

@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    pass

@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass

@admin.register(Paciente)
class PacienteAdmin(ModelAdmin):
    list_display = ('nome', 'data_nascimento', 'sexo')  # Campos exibidos na lista de pacientes

@admin.register(Procedimento)
class ProcedimentoAdmin(ModelAdmin):
    search_fields = ['codigo', 'nome']

@admin.register(ListaEsperaCirurgica)
class ListaEsperaCirurgicaAdmin(ModelAdmin):
    list_display = ('procedimentos__nome','paciente__nome', 'pontos')

    readonly_fields = ['pontos', 'data_entrada']
    
    autocomplete_fields = ['procedimentos']

    ordering = ('-pontos', )
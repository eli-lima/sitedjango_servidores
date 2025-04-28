from django.contrib import admin
from .models import Servidor, ServidorHistory

@admin.register(Servidor)
class ServidorAdmin(admin.ModelAdmin):
    list_display = (
        'matricula',
        'nome',
        'cargo',
        'local_trabalho',
        'regime',
        'status',
    )  # O que aparece na listagem

    list_filter = ('local_trabalho', 'regime', 'status', 'genero')  # Filtro lateral no admin

    search_fields = ('matricula', 'nome', 'email')  # Campos que podem ser buscados no admin

    autocomplete_fields = ['local_trabalho']  # Deixa o local_trabalho com autocomplete

    ordering = ('nome',)  # Ordena por nome por padrão

    fieldsets = (
        ('Informações Pessoais', {
            'fields': ('nome', 'matricula', 'data_nascimento', 'genero', 'telefone', 'email', 'endereco', 'foto_servidor')
        }),
        ('Informações Funcionais', {
            'fields': ('cargo', 'cargo_comissionado', 'simb_cargo_comissionado', 'regime', 'status', 'local_trabalho', 'lotacao', 'data_admissao', 'disposicao')
        }),
        ('Outros', {
            'fields': ('observacao',)
        }),
    )


admin.site.register(ServidorHistory)



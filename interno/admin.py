from django.contrib import admin
from .models import Interno


# Register your models here.

@admin.register(Interno)
class InternoAdmin(admin.ModelAdmin):
    # Definir quais campos aparecerão na listagem de Ajuda_Custo
    list_display = ('nome', 'prontuario', 'unidade', 'status')

    # Definir os campos que podem ser pesquisados (campo de pesquisa no topo da lista)
    search_fields = ('nome', 'prontuario', 'unidade')

    # Adicionar filtros laterais por unidade, carga horária e se é majorado ou não
    list_filter = ('unidade', 'status')

    # Habilitar a ordenação por data
    ordering = ('-prontuario',)
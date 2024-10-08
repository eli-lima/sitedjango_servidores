from django.contrib import admin
from .models import Ajuda_Custo, DataMajorada, LimiteAjudaCusto


@admin.register(Ajuda_Custo)
class AjudaCustoAdmin(admin.ModelAdmin):
    # Definir quais campos aparecerão na listagem de Ajuda_Custo
    list_display = ('nome', 'matricula', 'data', 'unidade', 'carga_horaria', 'majorado')

    # Definir os campos que podem ser pesquisados (campo de pesquisa no topo da lista)
    search_fields = ('nome', 'matricula', 'data')

    # Adicionar filtros laterais por unidade, carga horária e se é majorado ou não
    list_filter = ('unidade', 'carga_horaria', 'majorado', 'data')

    # Habilitar a ordenação por data
    ordering = ('-data',)


# Registrando outros modelos
admin.site.register(DataMajorada)
admin.site.register(LimiteAjudaCusto)

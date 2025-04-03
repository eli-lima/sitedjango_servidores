from django.contrib import admin
from rangefilter.filters import DateRangeFilter
from django.http import HttpRequest
from datetime import datetime
from .models import Ajuda_Custo, DataMajorada, LimiteAjudaCusto, CotaAjudaCusto


@admin.register(Ajuda_Custo)
class AjudaCustoAdmin(admin.ModelAdmin):
    # Configuração original dos campos de exibição
    list_display = ('nome', 'matricula', 'data', 'unidade', 'carga_horaria', 'majorado', 'codigo_verificacao')

    # Campos de pesquisa
    search_fields = ('nome', 'matricula', 'data')

    # Filtros (incluindo o DateRangeFilter corrigido)
    list_filter = (
        'unidade',
        'carga_horaria',
        'majorado',
        ('data', DateRangeFilter),  # Filtro de intervalo de datas
    )

    # Ordenação padrão
    ordering = ('-data',)

    # Correção do formato de data (método adicionado)
    def changelist_view(self, request, extra_context=None):
        if 'data__range__gte' in request.GET and 'data__range__lte' in request.GET:
            try:
                # Converte datas de DD/MM/YYYY para YYYY-MM-DD
                data_inicio = request.GET['data__range__gte']
                data_fim = request.GET['data__range__lte']

                data_inicio_formatada = datetime.strptime(data_inicio, '%d/%m/%Y').strftime('%Y-%m-%d')
                data_fim_formatada = datetime.strptime(data_fim, '%d/%m/%Y').strftime('%Y-%m-%d')

                request.GET = request.GET.copy()
                request.GET['data__range__gte'] = data_inicio_formatada
                request.GET['data__range__lte'] = data_fim_formatada
            except ValueError:
                pass  # Mantém o valor original se a conversão falhar

        return super().changelist_view(request, extra_context)


# Registrando outros modelos
admin.site.register(DataMajorada)
admin.site.register(LimiteAjudaCusto)
admin.site.register(CotaAjudaCusto)

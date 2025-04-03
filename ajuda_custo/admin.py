from django.contrib import admin
from rangefilter.filters import DateRangeFilter
from .models import Ajuda_Custo, DataMajorada, LimiteAjudaCusto, CotaAjudaCusto





@admin.register(Ajuda_Custo)
class AjudaCustoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'matricula', 'data', 'unidade', 'carga_horaria', 'majorado', 'codigo_verificacao')
    search_fields = ('nome', 'matricula', 'data')
    list_filter = (
        'unidade',
        'carga_horaria',
        'majorado',
        ('data', DateRangeFilter),  # Filtro de intervalo com calendário
    )
    ordering = ('-data',)


# Registrando outros modelos
admin.site.register(DataMajorada)
admin.site.register(LimiteAjudaCusto)
admin.site.register(CotaAjudaCusto)

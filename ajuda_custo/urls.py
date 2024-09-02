#urls - view - template

from django.urls import path, include
from .views import AjudaCusto, AjudaCustoAdicionar, RelatorioAjudaCusto, exportar_excel, excel_detalhado



app_name = 'ajuda_custo'

urlpatterns = [
    path('', AjudaCusto.as_view(), name='ajuda_custo'),
    path('adicionar/', AjudaCustoAdicionar.as_view(), name='adicionar'),
    path('relatorio/', RelatorioAjudaCusto.as_view(), name='relatorio_ajuda_custo'),
    path('exportar-excel/', exportar_excel, name='exportar_excel'),
    path('excel_detalhado/', excel_detalhado, name='excel_detalhado'),



]
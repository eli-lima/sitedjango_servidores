from django.urls import path
from .views import (RelatorioInterno, Internos, upload_planilha_excel, cadastrar_rosto,
                    reconhecer_interno, detalhes_interno, PopulacaoEdit)
from .htmx_views import interno_list

app_name = 'interno'

urlpatterns = [
    path('', Internos.as_view(), name='interno'),
    path('upload-interno/', upload_planilha_excel, name='upload_interno'),
    path('relatorio_interno/', RelatorioInterno.as_view(), name='relatorio_interno'),
    path('populacao-edit/', PopulacaoEdit.as_view(), name='populacao_edit'),
    path('<int:interno_id>/cadastrar-rosto/', cadastrar_rosto, name='cadastrar_rosto'),
    path('reconhecer-interno/', reconhecer_interno, name='reconhecer_interno'),
    path('<int:interno_id>/detalhes/', detalhes_interno, name='detalhes_interno'),  # Nova URL
]

htmx_urlpatterns = [
    path('interno_list/', interno_list, name='interno_list'),
]

urlpatterns += htmx_urlpatterns
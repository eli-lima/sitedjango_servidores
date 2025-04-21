from django.urls import path
from .views import (GestaoPrisional, OcorrenciaPlantaoAddView, buscar_servidor_list,
                    PopulacaoCarcerariaAPIView, RelatorioOcorrenciaPlantao, DetalhesOcorrenciaPlantao,
                    EditarOcorrenciaPlantao)


app_name = 'gestao_prisional'

urlpatterns = [
    # ocorrencias
    path('', GestaoPrisional.as_view(), name='gestao_prisional'),
    path('ocorrencia-plantao-add', OcorrenciaPlantaoAddView.as_view(), name='ocorrencia-plantao-add'),
    path('ocorrencia-detalhes/<int:pk>/', DetalhesOcorrenciaPlantao.as_view(), name='ocorrencia-detalhes'),
    path('ocorrencia-editar/<int:pk>/', EditarOcorrenciaPlantao.as_view(), name='ocorrencia-editar'),
    path('ocorrencia-relatorio/', RelatorioOcorrenciaPlantao.as_view(), name='ocorrencia-relatorio'),


    path('buscar-servidor-list/', buscar_servidor_list, name='buscar-servidor-list'),
    path('api/populacao-carceraria/', PopulacaoCarcerariaAPIView.as_view(), name='populacao-carceraria-api'),

    # path('upload-interno/', upload_planilha_excel, name='upload_interno'),
    # path('relatorio_interno/', RelatorioInterno.as_view(), name='relatorio_interno'),
    # path('populacao-edit/', PopulacaoEdit.as_view(), name='populacao_edit'),
    # path('<int:interno_id>/cadastrar-rosto/', cadastrar_rosto, name='cadastrar_rosto'),
    # path('reconhecer-interno/', reconhecer_interno, name='reconhecer_interno'),
    # path('<int:interno_id>/detalhes/', detalhes_interno, name='detalhes_interno'),  # Nova URL
]
#
# htmx_urlpatterns = [
#     path('interno_list/', interno_list, name='interno_list'),
# ]
#
# urlpatterns += htmx_urlpatterns
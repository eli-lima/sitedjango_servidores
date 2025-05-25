from django.urls import path
from .views import (Armaria, ArmamentoAddView, ArmamentoDetailView, ArmamentoEditView,
                    GerarTermoPDFView, RelatorioArmariaView, export_to_pdf_armamento,
                    ListaMunicoesView, IncluirLoteView, MovimentarMunicaoView, BaixarMunicaoView,
                    get_quantidade_disponivel)
from .htmx_views import armamento_list


app_name = 'armaria'

urlpatterns = [
    # ocorrencias
    path('', Armaria.as_view(), name='armaria'),
    path('armamento-add/', ArmamentoAddView.as_view(), name='armamento-add'),
    path('armamento/<int:pk>/', ArmamentoDetailView.as_view(), name='armamento_detail'),
    path('armamento/<int:pk>/gerar-termo/', GerarTermoPDFView.as_view(), name='gerar_termo'),
    path('armamento/<int:pk>/editar/', ArmamentoEditView.as_view(), name='armamento_edit'),
    path('relatorio/', RelatorioArmariaView.as_view(), name='relatorio_armaria'),
    path('export-to-pdf_armamento/', export_to_pdf_armamento, name='export_to_pdf_armamento'),
    path('municoes/', ListaMunicoesView.as_view(), name='lista_municoes'),
    path('municoes/incluir/', IncluirLoteView.as_view(), name='incluir_municao'),
    path('municoes/movimentar/', MovimentarMunicaoView.as_view(), name='movimentar_municao'),
    path('municoes/baixar/', BaixarMunicaoView.as_view(), name='baixar_municao'),
    path('ajax/get_quantidade_disponivel/', get_quantidade_disponivel, name='get_quantidade_disponivel'),
    # path('ocorrencia-plantao-add', OcorrenciaPlantaoAddView.as_view(), name='ocorrencia-plantao-add'),
    # path('ocorrencia-detalhes/<int:pk>/', DetalhesOcorrenciaPlantao.as_view(), name='ocorrencia-detalhes'),
    # path('ocorrencia-editar/<int:pk>/', EditarOcorrenciaPlantao.as_view(), name='ocorrencia-editar'),
    # path('ocorrencia-relatorio/', RelatorioOcorrenciaPlantao.as_view(), name='ocorrencia-relatorio'),
    #
    #
    # path('buscar-servidor-list/', buscar_servidor_list, name='buscar-servidor-list'),
    # path('api/populacao-carceraria/', PopulacaoCarcerariaAPIView.as_view(), name='populacao-carceraria-api'),

    # path('upload-interno/', upload_planilha_excel, name='upload_interno'),
    # path('relatorio_interno/', RelatorioInterno.as_view(), name='relatorio_interno'),
    # path('populacao-edit/', PopulacaoEdit.as_view(), name='populacao_edit'),
    # path('<int:interno_id>/cadastrar-rosto/', cadastrar_rosto, name='cadastrar_rosto'),
    # path('reconhecer-interno/', reconhecer_interno, name='reconhecer_interno'),
    # path('<int:interno_id>/detalhes/', detalhes_interno, name='detalhes_interno'),  # Nova URL
]
#
# htmx_urlpatterns = [
htmx_urlpatterns = [
    path('armamento_list/', armamento_list, name='armamento_list'),
]

urlpatterns += htmx_urlpatterns
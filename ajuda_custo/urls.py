#urls - view - template

from django.urls import path
from .views import AjudaCusto, AjudaCustoAdicionar, RelatorioAjudaCusto, exportar_excel, \
    excel_detalhado, AdminCadastrar, buscar_nome_servidor, \
    HorasLimite, excluir_limite, upload_excel_rx2, status_task,\
    VerificarCargaHoraria, CargaHorariaGerente

from .htmx_views import ajuda_custo_list




app_name = 'ajuda_custo'

urlpatterns = [
    path('', AjudaCusto.as_view(), name='ajuda_custo'),
    path('adicionar/', AjudaCustoAdicionar.as_view(), name='adicionar'),
    path('relatorio/', RelatorioAjudaCusto.as_view(), name='relatorio_ajuda_custo'),
    path('exportar-excel/', exportar_excel, name='exportar_excel'),
    path('excel_detalhado/', excel_detalhado, name='excel_detalhado'),
    path('admin_cadastrar/', AdminCadastrar.as_view(), name='admin_cadastrar'),
    path('buscar-nome-servidor/', buscar_nome_servidor, name='buscar_nome_servidor'),
    path('horas_limite/', HorasLimite.as_view(), name='horas_limite'),
    path('excluir-limite/<int:pk>/', excluir_limite, name='excluir_limite'),
    path('upload-excel_rx2/', upload_excel_rx2, name='upload_excel_rx2'),
    path('status_task/<str:task_id>/', status_task, name='status_task'),
    path('verificar_carga_horaria/', VerificarCargaHoraria.as_view(), name='verificar_carga_horaria'),
path('cargahoraria_gerente/', CargaHorariaGerente.as_view(), name='cargahoraria_gerente'),
]

htmx_urlpatterns = [
    path('ajuda_custo_list/', ajuda_custo_list,  name='ajuda_custo_list')
]


urlpatterns += htmx_urlpatterns
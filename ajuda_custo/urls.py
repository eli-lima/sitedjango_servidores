from django.urls import path
from .views import AjudaCusto, EnvioDatasView, ConfirmacaoDatasView, RelatorioAjudaCusto, exportar_excel, \
    excel_detalhado, AdminCadastrar, buscar_nome_servidor, \
    HorasLimite, excluir_limite, upload_excel_rx2, VerificarCargaHoraria, CargaHorariaGerente,\
    excluir_cota, reenviar_codigo, excluir_ajuda_custo, status_task  # Adicione status_task aqui
from .htmx_views import ajuda_custo_list


app_name = 'ajuda_custo'

urlpatterns = [
    path('', AjudaCusto.as_view(), name='ajuda_custo'),
    path('enviar/', EnvioDatasView.as_view(), name='envio_datas'),
    path('confirmacao/', ConfirmacaoDatasView.as_view(), name='confirmacao_datas'),
    path("reenviar_codigo/", reenviar_codigo, name="reenviar_codigo"),
    path('relatorio/', RelatorioAjudaCusto.as_view(), name='relatorio_ajuda_custo'),
    path('exportar-excel/', exportar_excel, name='exportar_excel'),
    path('excel_detalhado/', excel_detalhado, name='excel_detalhado'),
    path('admin_cadastrar/', AdminCadastrar.as_view(), name='admin_cadastrar'),
    path('buscar-nome-servidor/', buscar_nome_servidor, name='buscar_nome_servidor'),
    path('horas_limite/', HorasLimite.as_view(), name='horas_limite'),
    #exclusoes
    path('excluir-ajuda-custo/<int:pk>/', excluir_ajuda_custo, name='excluir_ajuda_custo'),
    path('excluir-limite/<int:pk>/', excluir_limite, name='excluir_limite'),
    path('excluir-cota/<int:pk>/', excluir_cota, name='excluir_cota'),
    path('upload-excel_rx2/', upload_excel_rx2, name='upload_excel_rx2'),
    path('verificar_carga_horaria/', VerificarCargaHoraria.as_view(), name='verificar_carga_horaria'),
    path('cargahoraria_gerente/', CargaHorariaGerente.as_view(), name='cargahoraria_gerente'),
    # Adicione esta nova linha para a view status_task
    path('status-task/<str:task_id>/', status_task, name='status_task'),
]

htmx_urlpatterns = [
    path('ajuda_custo_list/', ajuda_custo_list,  name='ajuda_custo_list')
]

urlpatterns += htmx_urlpatterns
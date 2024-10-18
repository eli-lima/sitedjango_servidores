#urls - view - template

from django.urls import path, include
from .views import RecursosHumanosPage, CriarServidorView, \
    ServidorEdit, export_to_pdf, ServidorLote, \
    RelatorioRh, ServidorDetail, check_task_status


app_name = 'servidor'

urlpatterns = [
    path('', RecursosHumanosPage.as_view(), name='recursos_humanos'),
    path('criar/', CriarServidorView.as_view(), name='criar_servidor'),
    path('edit/<int:pk>', ServidorEdit.as_view(), name='servidor_edit'),
    path('export-to-pdf/', export_to_pdf, name='export_to_pdf'),
    path('task-status/<str:task_id>/', check_task_status, name='task_status'),
    path('lote/', ServidorLote.as_view(), name='servidor_lote'),
    path('relatorio_rh', RelatorioRh.as_view(), name='relatorio_rh'),
    path('detail/<int:pk>', ServidorDetail.as_view(), name='servidor_detail'),






]
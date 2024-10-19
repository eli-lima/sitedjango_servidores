#urls - view - template

from django.urls import path, include
from .views import RecursosHumanosPage, CriarServidorView, \
    ServidorEdit, export_to_pdf, ServidorLote, \
    RelatorioRh, ServidorDetail, pdf_wait, check_task_status


app_name = 'servidor'

urlpatterns = [
    path('', RecursosHumanosPage.as_view(), name='recursos_humanos'),
    path('criar/', CriarServidorView.as_view(), name='criar_servidor'),
    path('edit/<int:pk>', ServidorEdit.as_view(), name='servidor_edit'),
    path('export-to-pdf/', export_to_pdf, name='export_to_pdf'),
    path('lote/', ServidorLote.as_view(), name='servidor_lote'),
    path('relatorio_rh', RelatorioRh.as_view(), name='relatorio_rh'),
    path('detail/<int:pk>', ServidorDetail.as_view(), name='servidor_detail'),
    path('pdf-wait/', pdf_wait, name='pdf_wait'),
    path('check-task/', check_task_status, name='check_task_status'),






]
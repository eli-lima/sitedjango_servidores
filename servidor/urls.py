#urls - view - template

from django.urls import path, include
from .views import RecursosHumanosPage, CriarServidorView, ServidorEdit, export_to_pdf

app_name = 'servidor'

urlpatterns = [
    path('', RecursosHumanosPage.as_view(), name='recursos_humanos'),
    path('criar/', CriarServidorView.as_view(), name='criar_servidor'),
    path('edit/<int:pk>', ServidorEdit.as_view(), name='servidor_edit'),
    path('export-to-pdf/', export_to_pdf, name='export_to_pdf'),






]
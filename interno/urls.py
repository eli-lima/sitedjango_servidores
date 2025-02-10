#urls - view - template

from django.urls import path
from .views import RelatorioInterno, Internos, upload_excel_internos, status_task_internos
from .htmx_views import interno_list

app_name = 'interno'


urlpatterns = [
    path('', Internos.as_view(), name='interno'),
    path('upload-interno/', upload_excel_internos, name='upload_internos'),
    path('status/<str:task_id>/', status_task_internos, name='status_task_internos'),
    path('relatorio_interno/', RelatorioInterno.as_view(), name='relatorio_interno'),
]

htmx_urlpatterns = [
    path('interno_list/', interno_list,  name='interno_list')
]


urlpatterns += htmx_urlpatterns
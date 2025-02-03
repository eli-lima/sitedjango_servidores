#urls - view - template

from django.urls import path
from .views import upload_pdfs, RelatorioInterno, Internos
from .htmx_views import interno_list

app_name = 'interno'


urlpatterns = [
    path('', Internos.as_view(), name='interno'),
    path('upload-interno/', upload_pdfs, name='upload_interno'),
    path('relatorio_interno/', RelatorioInterno.as_view(), name='relatorio_interno'),
]

htmx_urlpatterns = [
    path('interno_list/', interno_list,  name='interno_list')
]


urlpatterns += htmx_urlpatterns
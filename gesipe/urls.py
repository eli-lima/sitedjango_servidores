#urls - view - template

from django.urls import path, include
from .views import (Gesipe, GesipeAdm, GesipeAdmEdit,
                    GesipeAdmLote, GesipeArmaria,
                    GesipeSga, RelatorioGesipeAdm,
                    RelatorioGesipeSga, GesipeSgaAdd, GesipeSgaEdit,
                    GesipeSgaLote
                    )


app_name = 'gesipe'

urlpatterns = [
    path('', Gesipe.as_view(), name='gesipe'),
    path('gesipe_adm', GesipeAdm.as_view(), name='gesipe_adm'),
    path('gesipe_adm/edit/<int:pk>', GesipeAdmEdit.as_view(), name='gesipe_adm_edit'),
    path('gesipe_adm_lote/', GesipeAdmLote.as_view(), name='gesipe_adm_lote'),
    path('gesipe_armaria/', GesipeArmaria.as_view(), name='gesipe_armaria'),
    path('gesipe_sga/', GesipeSga.as_view(), name='gesipe_sga'),
    path('relatorio_gesipe_adm', RelatorioGesipeAdm.as_view(), name='relatorio_gesipe_adm'),
    path('relatorio_gesipe_adm/export_pdf/', RelatorioGesipeAdm.as_view(), name='relatorio_gesipe_adm_export_pdf'),
    path('gesipe_sga_add/', GesipeSgaAdd.as_view(), name='gesipe_sga_add'),
    path('gesipe_sga/edit/<int:pk>', GesipeSgaEdit.as_view(), name='gesipe_sga_edit'),
    path('relatorio_gesipe_sga', RelatorioGesipeSga.as_view(), name='relatorio_gesipe_sga'),
    path('gesipe_sga_lote/', GesipeSgaLote.as_view(), name='gesipe_sga_lote'),


]
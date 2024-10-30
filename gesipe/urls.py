#urls - view - template

from django.urls import path, include
from .views import (Gesipe, GesipeAdm, GesipeAdmEdit,
                    GesipeAdmLote, GesipeArmaria)


app_name = 'gesipe'

urlpatterns = [
    path('', Gesipe.as_view(), name='gesipe'),
    path('gesipe_adm', GesipeAdm.as_view(), name='gesipe_adm'),
    path('gesipe_adm/edit/<int:pk>', GesipeAdmEdit.as_view(), name='gesipe_adm_edit'),
    path('gesipe_adm_lote/', GesipeAdmLote.as_view(), name='gesipe_adm_lote'),
path('gesipe_armaria/', GesipeArmaria.as_view(), name='gesipe_armaria')



]
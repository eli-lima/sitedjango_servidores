#urls - view - template

from django.urls import path, include
from .views import Copen, ApreensaoAddView, OcorrenciaView, buscar_interno, filtrar_objetos_htmx, AtendimentoView, \
    CustodiaAddView, CustodiaEditView, MpAddView

app_name = 'copen'

urlpatterns = [
    path('', Copen.as_view(), name='copen'),
    path('atendimento/', AtendimentoView.as_view(), name='atendimento'),
    path('apreensao_add/', ApreensaoAddView.as_view(), name='apreensao_add'),
    path('ocorrencia/', OcorrenciaView.as_view(), name='ocorrencia'),
    path('custodia_add/', CustodiaAddView.as_view(), name='custodia_add'),
    path('custodia_edit/<int:pk>', CustodiaEditView.as_view(), name='custodia_edit'),
    #partials htmx
    path('buscar-interno/', buscar_interno, name='buscar-interno'),
    path('filtrar-objetos/', filtrar_objetos_htmx, name='filtrar-objetos'),
    path('mp_add/', MpAddView.as_view(), name='mp_add'),

]


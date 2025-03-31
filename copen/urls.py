#urls - view - template

from django.urls import path, include
from .views import Copen, ApreensaoAddView, OcorrenciaView, buscar_interno, filtrar_objetos_htmx, AtendimentoView, \
    CustodiaAddView, CustodiaEditView, MpAddView, ApreensaoRelatorioView, relatorio_resumido_apreensao

app_name = 'copen'

urlpatterns = [
    path('', Copen.as_view(), name='copen'),
    path('atendimento-add/', AtendimentoView.as_view(), name='atendimento-add'),
    path('apreensao-add/', ApreensaoAddView.as_view(), name='apreensao-add'),
    path('ocorrencia-add/', OcorrenciaView.as_view(), name='ocorrencia-add'),
    path('custodia-add/', CustodiaAddView.as_view(), name='custodia-add'),
    path('mp-add/', MpAddView.as_view(), name='mp-add'),
    path('custodia-edit/<int:pk>', CustodiaEditView.as_view(), name='custodia-edit'),
    #relatorios
    path('apreensao-relatorio/', ApreensaoRelatorioView.as_view(), name='apreensao-relatorio'),


    #pdf_relatorios
    path('relatorio-resumido-apreensao/', relatorio_resumido_apreensao, name='relatorio-resumido-apreensao'),

    #partials htmx
    path('buscar-interno/', buscar_interno, name='buscar-interno'),
    path('filtrar-objetos/', filtrar_objetos_htmx, name='filtrar-objetos'),


]


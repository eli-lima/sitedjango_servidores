#urls - view - template

from django.urls import path, include
from .views import Homepage, PesquisarSite

app_name = 'seappb'

urlpatterns = [
    path('', Homepage.as_view(), name='homepage'),
    path('pesquisa/', PesquisarSite.as_view(), name='pesquisarsite'),

]
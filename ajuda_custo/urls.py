#urls - view - template

from django.urls import path, include
from .views import AjudaCusto, AjudaCustoAdicionar



app_name = 'ajuda_custo'

urlpatterns = [
    path('', AjudaCusto.as_view(), name='ajuda_custo'),
    path('adicionar/', AjudaCustoAdicionar.as_view(), name='adicionar'),




]
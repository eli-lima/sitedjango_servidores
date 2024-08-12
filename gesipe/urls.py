#urls - view - template

from django.urls import path, include
from .views import Gesipe, GesipeAdmData


app_name = 'gesipe'

urlpatterns = [
    path('', Gesipe.as_view(), name='gesipe'),
    path('gesipe_adm/data/', GesipeAdmData.as_view(), name='gesipe_adm_data'),


]
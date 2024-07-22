#urls - view - template

from django.urls import path, include
from .views import Gesipe, Gesipe_adm_data


urlpatterns = [
    path('', Gesipe.as_view(), name='gesipe'),
    path('<int:pk>', Gesipe_adm_data.as_view(), name='gesipe_adm_data'),


]
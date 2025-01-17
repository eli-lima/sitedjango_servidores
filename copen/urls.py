#urls - view - template

from django.urls import path
from .views import Copen

app_name = 'copen'

urlpatterns = [
    path('', Copen.as_view(), name='copen'),
]


#urls - view - template

from django.urls import path, include
from .views import Homepage


urlpatterns = [
    path('', Homepage.as_view(), name='homepage'),

]
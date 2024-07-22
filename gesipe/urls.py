#urls - view - template

from django.urls import path, include
from .views import Gesipe


urlpatterns = [
    path('', Gesipe.as_view()),

]
#urls - view - template

from django.urls import path, include
from .views import Homepage, PesquisarSite
from django.contrib.auth import views as auth_view

app_name = 'seappb'

urlpatterns = [
    path('', Homepage.as_view(), name='homepage'),
    path('pesquisa/', PesquisarSite.as_view(), name='pesquisarsite'),
    path('login/', auth_view.LoginView.as_view(template_name="login.html"), name='login'),
    path('logout/', auth_view.LogoutView.as_view(template_name="logout.html"), name='logout'),

]
#urls - view - template

from django.urls import path, reverse_lazy
from .views import Homepage, PesquisarSite, Paginaperfil, Criarconta, CustomLoginView
from django.contrib.auth import views as auth_view

app_name = 'seappb'

urlpatterns = [
    path('', Homepage.as_view(), name='homepage'),
    path('pesquisa/', PesquisarSite.as_view(), name='pesquisarsite'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_view.LogoutView.as_view(template_name="logout.html"), name='logout'),
    path('editarperfil/<int:pk>', Paginaperfil.as_view(), name='editarperfil'),
    path('criarconta/', Criarconta.as_view(), name='criarconta'),
    path('mudarsenha/', auth_view.PasswordChangeView.as_view(template_name='editarperfil.html',
                                                            success_url=reverse_lazy('seappb:homepage')), name='mudarsenha'),
]
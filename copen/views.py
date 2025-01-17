from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

# Create your views here.


class Copen(LoginRequiredMixin, TemplateView):
    template_name = "copen.html"


    def test_func(self):
        user = self.request.user
        grupos_permitidos = ['Administrador', 'GerCopen']
        return user.groups.filter(name__in=grupos_permitidos).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)
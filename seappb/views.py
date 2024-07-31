from django.shortcuts import render, redirect
from .models import Usuario
from django.views.generic import TemplateView, ListView, FormView, UpdateView
from gesipe.models import Gesipe_adm
from datetime import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from .mixins import HideNavMixin
from django.contrib.auth.views import LoginView
from .forms import CriarContaForm
from django.urls import reverse_lazy, reverse
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import os

# Create your views here.


class Homepage(LoginRequiredMixin, TemplateView):
    template_name = "homepage.html"



class PesquisarSite(LoginRequiredMixin, ListView):
    template_name = "pesquisa.html"
    model = Gesipe_adm
    context_object_name = 'gesipe_adm_list'  # Nome do contexto para o modelo principal

    def get_queryset(self):
        termo_pesquisa = self.request.GET.get('query')
        if termo_pesquisa:
            formatos_data = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]
            data_pesquisa = None

            for formato in formatos_data:
                try:
                    data_pesquisa = datetime.strptime(termo_pesquisa, formato).date()
                    break
                except ValueError:
                    continue

            if data_pesquisa:
                object_list = Gesipe_adm.objects.filter(data=data_pesquisa)
            else:
                object_list = Gesipe_adm.objects.none()
        else:
            object_list = Gesipe_adm.objects.all()  # Retorna todos os objetos se nenhum termo de pesquisa for fornecido
        return object_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Adiciona mais contextos aqui, se necessário
        return context

class Paginaperfil(LoginRequiredMixin, UpdateView):
    model = Usuario
    template_name = 'editarperfil.html'
    fields = ['first_name', 'last_name', 'email', 'username', 'matricula', 'foto_perfil', 'setor']

    def form_valid(self, form):
        if self.request.FILES:
            foto_perfil = self.request.FILES['foto_perfil']

            # Abrir a imagem usando Pillow
            image = Image.open(foto_perfil)

            # Converter a imagem para RGB, se necessário
            if image.mode in ("RGBA", "P"):  # RGBA inclui transparência, P é para paletas
                image = image.convert("RGB")

            # Reduzir a resolução da imagem (ajustar conforme necessário)
            max_size = (300, 300)  # Define o tamanho máximo da imagem
            image.thumbnail(max_size, Image.LANCZOS)

            # Salvar a imagem em um buffer
            buffer = BytesIO()
            image.save(buffer, format='JPEG')

            # Criar um novo arquivo de imagem a partir do buffer
            file_buffer = ContentFile(buffer.getvalue())
            form.instance.foto_perfil.save(foto_perfil.name, file_buffer)



        return super().form_valid(form)

    def get_success_url(self):
        return reverse('seappb:homepage')



class Criarconta(HideNavMixin, FormView):
    template_name = 'criarconta.html'
    form_class = CriarContaForm
    success_url = reverse_lazy('seappb:login')  # Redirecionar para a página de login após a criação da conta

    def form_valid(self, form):
        usuario = form.save(commit=False)
        if self.request.FILES:
            usuario.foto_perfil = self.request.FILES['foto_perfil']
        usuario.save()
        return super().form_valid(form)




class CustomLoginView(HideNavMixin, LoginView):
    template_name = 'login.html'
#adicionar novas listas ao menu de pesquisar

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context[
    #         'outro_modelo_list'] = OutroModelo.objects.all()  # Adicione outros conjuntos de consultas conforme necessário
    #     context[
    #         'terceiro_modelo_list'] = TerceiroModelo.objects.all()  # Adicione outros conjuntos de consultas conforme necessário
    #     return context




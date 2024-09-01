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
from django.db import models
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from django.utils import timezone
import calendar
from django.db.models import Sum
from django.contrib import messages

import os

# Create your views here.


class Homepage(LoginRequiredMixin, TemplateView):
    template_name = "homepage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtendo os dados para o gráfico
        current_year = timezone.now().year
        monthly_totals = []

        for month in range(1, 13):
            monthly_total = Gesipe_adm.objects.filter(data__year=current_year, data__month=month).aggregate(total=models.Sum('total'))['total'] or 0
            monthly_totals.append(monthly_total)

        # Labels dos meses
        labels = [calendar.month_name[month] for month in range(1, 13)]

        # Obtendo os dados para o gráfico de pizza
        total_values = Gesipe_adm.objects.aggregate(
            total_memorando=Sum('total_memorando'),
            total_despacho=Sum('total_despacho'),
            total_oficio=Sum('total_oficio'),
            total_os=Sum('total_os'),
            processos=Sum('processos'),
            portarias=Sum('portarias')
        )

        pie_labels = [
            'Memorandos',
            'Despachos',
            'Ofícios',
            'OS',
            'Processos',
            'Portarias'
        ]
        pie_values = [
            total_values['total_memorando'] or 0,
            total_values['total_despacho'] or 0,
            total_values['total_oficio'] or 0,
            total_values['total_os'] or 0,
            total_values['processos'] or 0,
            total_values['portarias'] or 0,
        ]

        # Obtendo os últimos 12 registros de Gesipe_adm, ordenados por data de edição (decrescente)
        context['object_list'] = Gesipe_adm.objects.order_by('-data_edicao')[:12]

        # Passando os dados para o template
        context['labels_mensais'] = labels
        context['values_mensais'] = monthly_totals
        context['pie_labels'] = pie_labels
        context['pie_values'] = pie_values

        # Obtendo dados gerais para o gráfico de linha
        daily_totals = Gesipe_adm.objects.values('data') \
            .annotate(total=Sum('total')) \
            .order_by('data')

        # Separar labels e valores
        line_labels = [entry['data'].strftime("%d/%m/%Y") for entry in daily_totals]
        line_values = [entry['total'] for entry in daily_totals]

        # Passar os dados para o contexto
        context['line_labels'] = line_labels
        context['line_values'] = line_values



        return context


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
    fields = ['nome_completo', 'email', 'username', 'matricula', 'foto_perfil', 'setor']

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

    def form_valid(self, form):
        messages.success(self.request, 'Login realizado com sucesso!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Erro no login. Verifique suas credenciais e tente novamente.')
        return super().form_invalid(form)

#adicionar novas listas ao menu de pesquisar

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context[
    #         'outro_modelo_list'] = OutroModelo.objects.all()  # Adicione outros conjuntos de consultas conforme necessário
    #     context[
    #         'terceiro_modelo_list'] = TerceiroModelo.objects.all()  # Adicione outros conjuntos de consultas conforme necessário
    #     return context




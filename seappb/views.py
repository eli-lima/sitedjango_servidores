from django.shortcuts import render, redirect
from .models import Usuario
from django.views.generic import TemplateView, ListView, FormView, UpdateView
from gesipe.models import Gesipe_adm
from servidor.models import Servidor
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
from django.contrib.auth.models import Group
from django.db.models import Count
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q
from django.http import JsonResponse
from .forms import UnidadeForm


import os

# Create your views here.
def adicionar_unidade(request):
    if request.method == "POST":
        form = UnidadeForm(request.POST)

        if form.is_valid():
            try:
                unidade = form.save()
                print(f"✅ Unidade salva: {unidade}")
                return JsonResponse({"status": "success", "message": "Unidade cadastrada com sucesso!"})
            except Exception as e:
                print(f"❌ ERRO AO SALVAR: {e}")
                return JsonResponse({"status": "error", "message": str(e)}, status=500)
        else:
            print(f"⚠️ FORMULÁRIO INVÁLIDO: {form.errors}")
            return JsonResponse({"status": "error", "message": form.errors}, status=400)

    form = UnidadeForm()
    return render(request, "adicionar_unidade.html", {"form": form})





def custom_403(request, exception):
    # Adicionar 'hide_nav' ao contexto, como no HideNavMixin
    context = {
        'hide_nav': True
    }
    return render(request, '403.html', context, status=403)


class Homepage(LoginRequiredMixin, TemplateView):
    template_name = "homepage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['total_servidores'] = Servidor.objects.count()
        # Contar os servidores com o cargo 'POLICIAL PENAL'
        context['total_policiais_penal'] = Servidor.objects.filter(cargo='POLICIAL PENAL').count()

        # Contar os servidores com status "ativo" e cargo "Policial Penal"
        context['total_servidores_ativos_policial_penal'] = Servidor.objects.filter(
            status=True, cargo='POLICIAL PENAL').count()

        # Contar os servidores com status "inativo" e cargo "Policial Penal"
        context['total_servidores_inativos_policial_penal'] = Servidor.objects.filter(
            status=False, cargo='POLICIAL PENAL').count()


        # graficos do recursos humanos

        # Contar o número de servidores por gênero
        context['genero_masculino'] = Servidor.objects.filter(genero='M', cargo='POLICIAL PENAL').count()
        context['genero_feminino'] = Servidor.objects.filter(genero='F', cargo='POLICIAL PENAL').count()
        context['genero_outros'] = Servidor.objects.filter(genero='O', cargo='POLICIAL PENAL').count()

        # Labels e valores para o gráfico de pizza
        context['pie_labels'] = ['Masculino', 'Feminino', 'Outros']
        context['pie_values'] = [
            context['genero_masculino'],
            context['genero_feminino'],
            context['genero_outros']
        ]

        # Adicionar o gráfico de barras horizontal com efetivo por unidade
        efetivo_por_unidade = (
            Servidor.objects.filter(cargo='POLICIAL PENAL')
            .values('local_trabalho__nome')
            .annotate(total=Count('id'))
            .order_by('-total')
        )

        context['bar_labels'] = [item['local_trabalho__nome'] for item in efetivo_por_unidade]
        context['bar_values'] = [item['total'] for item in efetivo_por_unidade]

        # Obtendo os dados para o gráfico de barra administrativo
        current_year = timezone.now().year
        monthly_totals = []

        for month in range(1, 13):
            monthly_total = \
            Gesipe_adm.objects.filter(data__year=current_year, data__month=month).aggregate(total=models.Sum('total'))[
                'total'] or 0
            monthly_totals.append(monthly_total)

        # Labels dos meses
        # Dicionário com os nomes dos meses em português
        meses_em_portugues = {
            1: "Janeiro",
            2: "Fevereiro",
            3: "Março",
            4: "Abril",
            5: "Maio",
            6: "Junho",
            7: "Julho",
            8: "Agosto",
            9: "Setembro",
            10: "Outubro",
            11: "Novembro",
            12: "Dezembro"
        }
        labels_mensais = [meses_em_portugues[month] for month in range(1, 13)]

        # Obtendo os dados para o gráfico de pizza administrativo
        total_values = Gesipe_adm.objects.aggregate(
            diarias=Sum('diarias'),
            documentos_capturados=Sum('documentos_capturados'),
            total_despacho=Sum('total_despacho'),
            total_oficio=Sum('total_oficio'),
            total_os=Sum('total_os'),
            processos=Sum('processos'),
            portarias=Sum('portarias')
        )

        pie_labels_adm = [
            'Diárias',
            'Documentos Capturados',
            'Despachos',
            'Ofícios',
            'OS',
            'Processos',
            'Portarias'
        ]
        pie_values_adm = [
            total_values['diarias'] or 0,
            total_values['documentos_capturados'] or 0,
            total_values['total_despacho'] or 0,
            total_values['total_oficio'] or 0,
            total_values['total_os'] or 0,
            total_values['processos'] or 0,
            total_values['portarias'] or 0,
        ]

        # Obtendo os últimos 12 registros de Gesipe_adm, ordenados por data de edição (decrescente)
        context['object_list'] = Gesipe_adm.objects.order_by('-data')[:12]

        # Passando os dados para o template
        context['labels_mensais'] = labels_mensais
        context['values_mensais'] = monthly_totals
        context['pie_labels_adm'] = pie_labels_adm
        context['pie_values_adm'] = pie_values_adm

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

    def get_form(self):
        form = super().get_form()
        form.fields['email'].widget.attrs['readonly'] = True
        form.fields['email'].widget.attrs['style'] = 'background-color: #f0f0f0;' # Fundo cinza
        form.fields['matricula'].widget.attrs['readonly'] = True
        form.fields['matricula'].widget.attrs['style'] = 'background-color: #f0f0f0;'  # Fundo cinza
        return form

    def get_success_url(self):
        return reverse('seappb:homepage')


class Criarconta(HideNavMixin, FormView):
    template_name = 'criarconta.html'
    form_class = CriarContaForm
    success_url = reverse_lazy('seappb:login')  # Redirecionar para a página de login após a criação da conta

    def form_valid(self, form):
        # Salva o usuário com a lógica personalizada do formulário
        usuario = form.save(commit=False)

        # Se houver foto de perfil, ela será associada
        if self.request.FILES:
            usuario.foto_perfil = self.request.FILES['foto_perfil']

        # Salva o usuário
        usuario.save()

        # Adiciona o usuário ao grupo "Padrao" após salvar
        padrao_group = Group.objects.get(name="Padrao")
        usuario.groups.add(padrao_group)

        # Exibe a mensagem de sucesso
        messages.success(self.request, 'Conta criada com sucesso! Você pode agora fazer login.')

        # Redireciona para a página de login
        return super().form_valid(form)

    def form_invalid(self, form):
        # Se houver erro, exibe a mensagem de erro no formulário
        messages.error(self.request, 'Houve um erro ao criar sua conta. Verifique os dados inseridos.')
        return super().form_invalid(form)


class CustomLoginView(HideNavMixin, LoginView):
    template_name = 'login.html'

    def form_valid(self, form):
        messages.success(self.request, 'Login realizado com sucesso!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Erro no login. Verifique suas credenciais e tente novamente.')
        return super().form_invalid(form)

    def get_success_url(self):
        user = self.request.user
        if user.groups.filter(Q(name='Administrador') | Q(name='Gergesipe')).exists():
            return reverse('seappb:homepage')
        elif user.groups.filter(name='Padrao').exists():
            return reverse('ajuda_custo:ajuda_custo')
        else:
            return reverse('seappb:homepage')  # Redirecionamento padrão


class Estatisticas(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "estatisticas.html"

    def test_func(self):
        user = self.request.user
        # Define os grupos permitidos
        grupos_permitidos = ['Administrador', 'GerGesipe']
        # Retorna True se o usuário pertence a pelo menos um dos grupos
        return user.groups.filter(name__in=grupos_permitidos).exists()

        # Levanta exceção em caso de falta de permissão

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)  # Substitua '404.html' pelo nome do seu template



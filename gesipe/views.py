from django.shortcuts import render, redirect
from .models import Gesipe_adm
from django.views.generic.edit import FormView
from django.utils.timezone import now
from .forms import GesipeAdmForm, BuscaDataForm
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q  # Para pesquisas com OR lógico
from django.utils import timezone
from django.contrib import messages


# Create your views here.

# url - view - html


class Gesipe(LoginRequiredMixin, ListView):
    template_name = "gesipe.html"
    model = Gesipe_adm
    paginate_by = 5  # Itens por página
    ordering = ['data']  # Ordena pelo campo 'data'

    def get_queryset(self):
        query = self.request.GET.get('query', '')
        queryset = super().get_queryset()

        if query:
            queryset = queryset.filter(
                Q(usuario__username__icontains=query) |  # Filtra pelo nome de usuário
                Q(data__icontains=query) |  # Filtra pela data
                Q(total__icontains=query)  # Filtra pelo total de inserções
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('query', '')
        return context


class GesipeAdmData(FormView):
    template_name = 'gesipe_adm_data.html'
    form_class = BuscaDataForm
    form_class_data = GesipeAdmForm

    def get(self, request, *args, **kwargs):
        form_busca = self.form_class()
        form_data = self.form_class_data()
        mostrar_formulario = False

        if 'data' in request.GET:
            data = request.GET['data']
            print(f"Data recebida na GET: {data}")

            dados_adm = Gesipe_adm.objects.filter(data=data).first()
            print(f"Dados encontrados: {dados_adm}")

            mostrar_formulario = True
            if dados_adm:
                form_data = self.form_class_data(instance=dados_adm)
                print(f"Formulário preenchido com dados existentes: {form_data.initial}")
            else:
                form_data = self.form_class_data(initial={
                    'data': data,
                    'processos': 0,
                    'memorandos_diarias': 0,
                    'memorandos_documentos_capturados': 0,
                    'despachos_gerencias': 0,
                    'despachos_unidades': 0,
                    'despachos_grupos': 0,
                    'oficios_internos_unidades_prisionais': 0,
                    'oficios_internos_setores_seap_pb': 0,
                    'oficios_internos_circular': 0,
                    'oficios_externos_seap_pb': 0,
                    'oficios_externos_diversos': 0,
                    'oficios_externos_judiciario': 0,
                    'os_grupos': 0,
                    'os_diversos': 0,
                    'portarias': 0,
                })
                print(f"Formulário inicial com valores padrão: {form_data.initial}")

        return self.render_to_response({
            'form_busca': form_busca,
            'form_data': form_data,
            'mostrar_formulario': mostrar_formulario
        })

    def post(self, request, *args, **kwargs):
        form_busca = self.form_class(request.POST)
        form_data = self.form_class_data(request.POST)
        mostrar_formulario = False

        if form_busca.is_valid() and 'botao_buscar' in request.POST:
            data = form_busca.cleaned_data['data']
            print(f"Data recebida na POST (busca): {data}")

            dados_adm = Gesipe_adm.objects.filter(data=data).first()
            print(f"Dados encontrados para busca: {dados_adm}")

            mostrar_formulario = True
            if dados_adm:
                form_data = self.form_class_data(instance=dados_adm)
                print(f"Formulário preenchido com dados existentes: {form_data.initial}")
            else:
                form_data = self.form_class_data(initial={
                    'data': data,
                    'processos': 0,
                    'memorandos_diarias': 0,
                    'memorandos_documentos_capturados': 0,
                    'despachos_gerencias': 0,
                    'despachos_unidades': 0,
                    'despachos_grupos': 0,
                    'oficios_internos_unidades_prisionais': 0,
                    'oficios_internos_setores_seap_pb': 0,
                    'oficios_internos_circular': 0,
                    'oficios_externos_seap_pb': 0,
                    'oficios_externos_diversos': 0,
                    'oficios_externos_judiciario': 0,
                    'os_grupos': 0,
                    'os_diversos': 0,
                    'portarias': 0,
                })
                print(f"Formulário inicial com valores padrão: {form_data.initial}")

        if form_data.is_valid():
            data = form_data.cleaned_data['data']
            print(f"Data para salvar/atualizar: {data}")

            dados_adm = Gesipe_adm.objects.filter(data=data).first()
            print(f"Dados encontrados para atualizar: {dados_adm}")

            if dados_adm:
                form_data = self.form_class_data(request.POST, instance=dados_adm)
                print(f"Formulário atualizado com dados existentes: {form_data.cleaned_data}")
            else:
                form_data = self.form_class_data(request.POST)

            if form_data.is_valid():
                print("Formulário é válido. Salvando dados...")
                dados_adm = form_data.save(commit=False)
                dados_adm.usuario = request.user  # Define o usuário atual
                dados_adm.data_edicao = timezone.now()  # Atualiza a data de edição
                dados_adm.save()
                messages.success(self.request, 'Dados Adicionados/Atualizados com Sucesso')
                return redirect('gesipe:gesipe_adm_data')
            else:
                print(f"Erros no formulário de dados: {form_data.errors}")

        return self.render_to_response({
            'form_busca': form_busca,
            'form_data': form_data,
            'mostrar_formulario': mostrar_formulario
        })
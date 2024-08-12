from django.shortcuts import render, redirect
from .models import Gesipe_adm
from django.views.generic.edit import FormView
from django.utils.timezone import now
from .forms import GesipeAdmForm, BuscaDataForm
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q  # Para pesquisas com OR lógico

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


class GesipeAdmData(LoginRequiredMixin, FormView):
    template_name = 'gesipe_adm_data.html'
    form_class = BuscaDataForm
    form_class_data = GesipeAdmForm

    def get(self, request, *args, **kwargs):
        form_busca = self.form_class()
        form_data = self.form_class_data()
        mostrar_formulario = False

        if 'data' in request.GET:
            data = request.GET['data']
            dados_adm = Gesipe_adm.objects.filter(data=data).first()
            mostrar_formulario = True
            if dados_adm:
                form_data = self.form_class_data(instance=dados_adm)

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
            dados_adm = Gesipe_adm.objects.filter(data=data).first()
            mostrar_formulario = True
            if dados_adm:
                form_data = self.form_class_data(instance=dados_adm)

        if form_data.is_valid() and 'botao_submit' in request.POST:
            dados_adm, created = Gesipe_adm.objects.get_or_create(
                data=form_data.cleaned_data['data'],
                defaults={'usuario': self.request.user}  # Adiciona o usuário ao criar
            )

            for field in form_data.fields:
                setattr(dados_adm, field, form_data.cleaned_data[field])
            dados_adm.total = (
                    dados_adm.processos + dados_adm.memorandos_diarias +
                    dados_adm.memorandos_documentos_capturados + dados_adm.despachos_gerencias +
                    dados_adm.despachos_unidades + dados_adm.despachos_grupos +
                    dados_adm.oficios_internos_unidades_prisionais + dados_adm.oficios_internos_setores_seap_pb +
                    dados_adm.oficios_internos_circular + dados_adm.oficios_externos_seap_pb +
                    dados_adm.oficios_externos_diversos + dados_adm.oficios_externos_judiciario +
                    dados_adm.os_grupos + dados_adm.os_diversos + dados_adm.portarias
            )
            dados_adm.usuario = self.request.user  # Define o usuário antes de salvar
            dados_adm.save()
            return redirect('gesipe_adm_data')

        return self.render_to_response({
            'form_busca': form_busca,
            'form_data': form_data,
            'mostrar_formulario': mostrar_formulario
        })


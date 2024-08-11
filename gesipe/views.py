from django.shortcuts import render
from .models import Gesipe_adm
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



class Gesipe_adm_data(LoginRequiredMixin, DetailView):
    template_name = "gesipe_adm_data.html"
    model = Gesipe_adm
    #object -> item especifico do modelo


    # vou usar para somar a quantidade de edicoes dos usuarios
    # def get(self, request, *args, **kwargs):
    #     #descobrir qual data esta editando ou adicionando
    #     data = self.get.object()
    #     data.visualizacoes += 1
    #     data.save()
    #
    #     return super().get(request, *args, **kwargs) #redireciona o usuario para a url final

    def get_context_data(self, **kwargs):
        context = super(Gesipe_adm_data, self).get_context_data(**kwargs)
        #adicionar novos dados a pagina que nao faz referencial ao Detailview
        #self.get_object()
        return context


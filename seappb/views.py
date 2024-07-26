from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from gesipe.models import Gesipe_adm
from datetime import datetime
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.
# def homepage(request):
#     return render(request, "homepage.html")

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

class Paginaperfil(LoginRequiredMixin, TemplateView):
    template_name = 'editarperfil.html'

class Criarconta( TemplateView):
    template_name = 'criarconta.html'



#adicionar novas listas ao menu de pesquisar

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context[
    #         'outro_modelo_list'] = OutroModelo.objects.all()  # Adicione outros conjuntos de consultas conforme necessário
    #     context[
    #         'terceiro_modelo_list'] = TerceiroModelo.objects.all()  # Adicione outros conjuntos de consultas conforme necessário
    #     return context




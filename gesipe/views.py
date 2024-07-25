from django.shortcuts import render
from .models import Gesipe_adm
from django.views.generic import ListView, DetailView

# Create your views here.

# url - view - html
# def gesipe(request):
#     context = {}
#     lista_datas = Gesipe_adm.objects.all()
#     context ['lista_datas'] = lista_datas
#     return render(request, "gesipe.html", context)

class Gesipe(ListView):
    template_name = "gesipe.html"
    model = Gesipe_adm
    #object list -> lista de itens do modelo



class Gesipe_adm_data(DetailView):
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


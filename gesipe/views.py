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
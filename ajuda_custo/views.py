from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, CreateView, FormView, ListView
from .models import Ajuda_Custo, DataMajorada
from .forms import AjudaCustoForm
from django.urls import reverse_lazy
from datetime import datetime
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404

# Create your views here.


class AjudaCusto(LoginRequiredMixin, ListView):
    model = Ajuda_Custo
    template_name = "ajuda_custo.html"
    context_object_name = 'datas'
    paginate_by = 10  # Quantidade de registros por página

    def get_queryset(self):
        query = self.request.GET.get('query')
        if query:
            return Ajuda_Custo.objects.filter(
                Q(nome__icontains=query) | Q(matricula__icontains=query)
            ).order_by('nome')  # Ordena por nome
        return Ajuda_Custo.objects.all().order_by('nome')  # Ordena por nome


class AjudaCustoAdicionar(LoginRequiredMixin, FormView):
    model = Ajuda_Custo
    form_class = AjudaCustoForm
    template_name = 'ajuda_custo_add.html'
    success_url = reverse_lazy('ajuda_custo:ajuda_custo')

    def post(self, request, *args, **kwargs):
        form = self.get_form()

        if form.is_valid():
            mes = request.POST.get('mes')
            ano = request.POST.get('ano')

            dias = request.POST.getlist('dia')
            unidades = request.POST.getlist('unidade')
            cargas_horarias = request.POST.getlist('carga_horaria')

            for dia, unidade, carga_horaria in zip(dias, unidades, cargas_horarias):
                data_completa = datetime.strptime(f"{dia}/{mes}/{ano}", "%d/%m/%Y").date()

                # Verifica se a data existe no modelo DataMajorada
                majorado = DataMajorada.objects.filter(data=data_completa).exists()

                # Cria o objeto Ajuda_Custo e salva no banco de dados
                ajuda_custo = Ajuda_Custo(
                    matricula=self.request.user.matricula,
                    nome=self.request.user.nome_completo,
                    data=data_completa,
                    unidade=unidade,
                    carga_horaria=carga_horaria,
                    majorado=majorado  # Define como True se a data estiver em DataMajorada
                )
                ajuda_custo.save()

            messages.success(self.request, 'Datas adicionadas com sucesso!')
            return redirect(self.success_url)
        else:
            messages.error(self.request, 'Erro no Cadastro, Confira os Dados e Tente Novamente.')
            return self.form_invalid(form)
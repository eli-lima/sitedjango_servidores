from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UploadPDFForm
from .models import ArquivoUpload, Interno
from .utils import extrair_dados_pdf, salvar_dados
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import ListView
from django.db.models import Q


def upload_pdfs(request):
    if request.method == 'POST':
        form = UploadPDFForm(request.POST, request.FILES)
        if form.is_valid():
            arquivos = request.FILES.getlist('arquivos')
            for arquivo in arquivos:
                # Salvar o arquivo no modelo ArquivoUpload
                arquivo_model = ArquivoUpload.objects.create(arquivo=arquivo)

                # Processar o arquivo PDF
                dados = extrair_dados_pdf(arquivo_model.arquivo.path)
                salvar_dados(dados)

                # Marcar o arquivo como processado
                arquivo_model.processado = True
                arquivo_model.save()

            messages.success(request, 'Arquivos processados com sucesso!')
            return redirect('interno:upload_interno')

    else:
        form = UploadPDFForm()
    return render(request, 'upload_interno.html', {'form': form})



class Internos(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Interno
    template_name = "Interno.html"
    context_object_name = 'datas'
    paginate_by = 50  # Quantidade de registros por página

    def test_func(self):
        user = self.request.user
        grupos_permitidos = ['Administrador', 'Copen']
        return user.groups.filter(name__in=grupos_permitidos).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)

    def get_queryset(self):
        query = self.request.GET.get('query', '')

        queryset = Interno.objects.all()

        if query:
            queryset = queryset.filter(
                Q(nome__icontains=query)
            )

        # #filtro por unidade:
        #
        unidade = self.request.GET.get('unidade')
        if unidade:
            queryset = queryset.filter(unidade=unidade)

        cpf = self.request.GET.get('cpf')
        if cpf:
            queryset = queryset.filter(cpf=cpf)

        nome_mae = self.request.GET.get('nome_mae')
        if nome_mae:
            queryset = queryset.filter(
                Q(nome__icontains=query)
            )

        return queryset.order_by('-prontuario')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)



        return context





class RelatorioInterno(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Interno
    template_name = "relatorio_interno.html"
    context_object_name = 'datas'
    paginate_by = 50  # Quantidade de registros por página

    def test_func(self):
        user = self.request.user
        grupos_permitidos = ['Administrador', 'Copen']
        return user.groups.filter(name__in=grupos_permitidos).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)

    def get_queryset(self):
        query = self.request.GET.get('query', '')




        queryset = Interno.objects.all()

        if query:
            queryset = queryset.filter(
                Q(nome__icontains=query)
            )

        # #filtro por unidade:
        #
        unidade = self.request.GET.get('unidade')
        if unidade:
            queryset = queryset.filter(unidade=unidade)

        cpf = self.request.GET.get('cpf')
        if cpf:
            queryset = queryset.filter(cpf=cpf)

        nome_mae = self.request.GET.get('nome_mae')
        if nome_mae:
            queryset = queryset.filter(
                Q(nome__icontains=query)
            )

        return queryset.order_by('-prontuario')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Paginação personalizada
        page_obj = context['page_obj']
        paginator = page_obj.paginator
        page_range = paginator.page_range

        # Lógica para limitar a exibição das páginas
        if page_obj.number > 3:
            start = page_obj.number - 2
        else:
            start = 1

        if page_obj.number < paginator.num_pages - 2:
            end = page_obj.number + 2
        else:
            end = paginator.num_pages

        context['page_range'] = range(start, end + 1)

        interno = Interno.objects.all()
        context['interno'] = interno

        context['query'] = self.request.GET.get('query', '')

        # # Ajuste aqui: mudando 'unidade' para 'unidades'
        context['unidades'] = Interno.objects.values_list('unidade', flat=True).distinct().order_by('-unidade')

        # context['carga_horarias'] = Ajuda_Custo.objects.values_list('carga_horaria', flat=True).distinct()

        return context


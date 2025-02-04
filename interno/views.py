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
        print("📥 Recebendo requisição POST para upload de PDFs...")  # Debug

        form = UploadPDFForm(request.POST, request.FILES)
        if form.is_valid():
            print("✅ Formulário válido!")  # Debug

            arquivos = request.FILES.getlist('arquivos')
            print(f"📂 Número de arquivos recebidos: {len(arquivos)}")  # Debug

            for arquivo in arquivos:
                print(f"🔹 Processando arquivo: {arquivo.name}")  # Debug

                try:
                    # Criando instância no banco
                    arquivo_model = ArquivoUpload.objects.create(arquivo=arquivo)
                    print(f"💾 Arquivo salvo no banco: {arquivo_model.arquivo.path}")  # Debug

                    # Extraindo dados do PDF
                    dados = extrair_dados_pdf(arquivo_model.arquivo.path)
                    print(f"📄 Dados extraídos: {dados}")  # Debug

                    # Salvando os dados processados
                    salvar_dados(dados)
                    print("✅ Dados salvos com sucesso!")  # Debug

                    # Marcando como processado
                    arquivo_model.processado = True
                    arquivo_model.save()
                    print("🔄 Arquivo marcado como processado.")  # Debug

                except Exception as e:
                    print(f"❌ Erro ao processar o arquivo {arquivo.name}: {e}")  # Debug
                    messages.error(request, f"Erro ao processar {arquivo.name}: {e}")
                    return redirect('interno:upload_interno')

            messages.success(request, 'Arquivos processados com sucesso!')
            return redirect('interno:upload_interno')

        else:
            print("❌ Formulário inválido:", form.errors)  # Debug

    else:
        print("📄 Acessando página de upload.")  # Debug
        form = UploadPDFForm()

    return render(request, 'upload_interno.html', {'form': form})


class Internos(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Interno
    template_name = "interno.html"
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


        queryset = Interno.objects.all()


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


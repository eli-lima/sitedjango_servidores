from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UploadPDFForm, UploadExcelInternosForm
from .models import ArquivoUpload, Interno
from .utils import extrair_dados_pdf, salvar_dados
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import ListView
from django.db.models import Q
from .tasks import process_excel_internos
import traceback
from celery.result import AsyncResult
import cloudinary.uploader


def upload_excel_internos(request):
    print("Função upload_excel_internos chamada")  # Verifica se a função está sendo chamada

    if request.method == 'POST':
        print("Método POST detectado")  # Confirma que o método POST está sendo recebido
        form = UploadExcelInternosForm(request.POST, request.FILES)
        print(f"request.FILES: {request.FILES}")

        if form.is_valid():
            print("Formulário válido")  # Confirma que o formulário foi validado corretamente

            if 'arquivo' in request.FILES:
                excel_file = request.FILES['arquivo']
                print(f"Arquivo recebido: {excel_file.name}")  # Mostra o nome do arquivo enviado

                try:
                    print("Iniciando upload para Cloudinary...")
                    upload_result = cloudinary.uploader.upload(excel_file, resource_type="raw")
                    cloudinary_url = upload_result['url']
                    print(f"Arquivo enviado para Cloudinary: {cloudinary_url}")

                    # Chama a task de processamento
                    print("Enviando task para processamento...")
                    task = process_excel_internos.delay(cloudinary_url)
                    print(f"Task ID: {task.id}")


                    return redirect('interno:status_task_internos', task_id=task.id)


                except Exception as e:
                    erro_msg = f"Erro ao fazer upload: {str(e)}\n{traceback.format_exc()}"
                    print(erro_msg)
                    messages.error(request, erro_msg)
                    return redirect('interno:upload_excel_internos')


            else:
                print("Nenhum arquivo recebido no request.FILES")  # Indica se nenhum arquivo foi enviado
                messages.error(request, "Nenhum arquivo foi enviado.")
                return redirect('interno:upload_excel_internos')

        else:
            print("Formulário inválido")  # Indica se o formulário falhou na validação
            print(form.errors)  # Mostra os erros do formulário para depuração
            messages.error(request, "Formulário inválido. Verifique os dados enviados.")
            return redirect('interno:upload_excel_internos')

    else:
        print("Método GET recebido")  # Confirma que a página foi carregada via GET

    form = UploadExcelInternosForm()
    return render(request, 'upload_excel_internos.html', {'form': form})


def status_task_internos(request, task_id):
    task = AsyncResult(task_id)
    novos_inseridos = 0
    atualizados = 0

    if task.state == 'PENDING':
        status = "Processamento pendente..."
    elif task.state == 'SUCCESS':
        result = task.result
        status = "Concluído com sucesso!" if result['status'] == 'sucesso' else f"Erros: {', '.join(result['erros'])}"

        # Corrigido: Pegando os valores corretos do dicionário result
        if result['status'] == 'sucesso':
            novos_inseridos = result.get('total_novos', 0)
            atualizados = result.get('total_atualizados', 0)

    elif task.state == 'FAILURE':
        status = f"Falha no processamento: {task.result}"
    else:
        status = f"Em andamento... Status: {task.state}"

    return render(request, 'status_task_internos.html', {
        'status': status,
        'novos_inseridos': novos_inseridos if task.state == 'SUCCESS' else None,
        'atualizados': atualizados if task.state == 'SUCCESS' else None,
    })






class Internos(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Interno
    template_name = "interno.html"
    context_object_name = 'datas'
    paginate_by = 50  # Quantidade de registros por página

    def test_func(self):
        user = self.request.user
        grupos_permitidos = ['Administrador', 'Copen', 'GerGesipe']
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


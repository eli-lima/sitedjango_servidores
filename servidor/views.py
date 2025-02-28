from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, CreateView, ListView, UpdateView, View, DetailView
from .forms import ServidorForm, UploadFileForm, DocumentoForm
from django.urls import reverse_lazy
from django.contrib import messages
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from .models import Servidor, ServidorHistory, Documento
from django.db.models import Q, Count
import openpyxl
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from .tasks import generate_pdf
from django.shortcuts import render
from django.http import JsonResponse, FileResponse, HttpResponse, HttpResponseRedirect
import os
from django.conf import settings
from celery.result import AsyncResult
from seappb.models import Unidade

#deletar documentos


def documento_delete(request, documento_id):
    documento = get_object_or_404(Documento, id=documento_id)

    # Verifica se o usuário possui permissões necessárias (se necessário)
    if not request.user.has_perm('app.delete_documento'):
        messages.error(request, "Você não tem permissão para excluir este documento.")
        return redirect('servidor:servidor_detail', pk=documento.servidor.id)

    # Exclui o arquivo do sistema de arquivos e do banco de dados
    if documento.arquivo:
        documento.arquivo.delete()  # Remove o arquivo do sistema de arquivos
    documento.delete()  # Remove o registro do banco de dados

    # Adiciona uma mensagem de sucesso e redireciona
    messages.success(request, "Documento excluído com sucesso.")
    return redirect('servidor:servidor_edit', pk=documento.servidor.id)



# Create your views here.

#Relatorios PDF

@login_required
def export_to_pdf(request):
    try:
        # Buscar servidores e aplicar filtros
        servidores = Servidor.objects.all().order_by('nome')
        query = request.GET.get('query')
        if query:
            servidores = servidores.filter(Q(nome__icontains=query) | Q(matricula__icontains=query))
        cargo = request.GET.get('cargo')
        if cargo:
            servidores = servidores.filter(cargo=cargo)
        local_trabalho = request.GET.get('local_trabalho')
        if local_trabalho:
            local_trabalho_id = Unidade.objects.get(nome=local_trabalho).id
            servidores = servidores.filter(local_trabalho=local_trabalho_id)  # Filtrar pelo ID encontrado
        cargo_comissionado = request.GET.get('cargo_comissionado')
        if cargo_comissionado:
            servidores = servidores.filter(cargo_comissionado=cargo_comissionado)
        status = request.GET.get('status')
        if status:
            servidores = servidores.filter(status=status)
        genero = request.GET.get('genero')
        if genero:
            servidores = servidores.filter(genero=genero)

        # Converter QuerySet em lista de dicionários
        servidores = list(servidores.values('nome', 'matricula', 'cargo', 'local_trabalho', 'cargo_comissionado', 'status', 'genero'))

        # Definir o caminho do template
        template_path = 'servidor_pdf.html'

        # Iniciar a tarefa Celery para gerar o PDF
        result = generate_pdf.delay(servidores, template_path)
        print(f"Tarefa Celery iniciada com ID: {result.id}")

        # Redirecionar para uma página de espera, passando o ID da tarefa
        return HttpResponseRedirect(f'/servidor/pdf-wait/?task_id={result.id}')

    except Exception as e:
        print(f"Error in export_to_pdf view: {e}")
        return HttpResponse('Erro ao gerar PDF', status=500)


def pdf_wait(request):
    task_id = request.GET.get('task_id')
    print(f"Página de espera carregada com task_id: {task_id}")
    return render(request, 'pdf_wait.html', {'task_id': task_id})


def check_task_status(request):
    task_id = request.GET.get('task_id')
    print(f"Verificando status da tarefa com task_id: {task_id}")

    task = AsyncResult(task_id)

    if task.state == 'SUCCESS':
        print(f"Tarefa concluída com sucesso. URL do PDF: {task.result}")
        return JsonResponse({'status': 'SUCCESS', 'url': task.result})
    elif task.state == 'FAILURE':
        print("Falha ao gerar o PDF.")
        return JsonResponse({'status': 'FAILURE'})
    else:
        print(f"Status da tarefa: {task.state}")
        return JsonResponse({'status': task.state})


class RecursosHumanosPage(LoginRequiredMixin, ListView):
    model = Servidor
    template_name = "servidor.html"
    context_object_name = 'servidores'
    paginate_by = 10  # Quantidade de registros por página

    def get_queryset(self):
        query = self.request.GET.get('query')
        if query:
            return Servidor.objects.filter(
                Q(nome__icontains=query) | Q(matricula__icontains=query),
                cargo='POLICIAL PENAL'  # Filtrar apenas servidores com cargo 'POLICIAL PENAL'
            ).order_by('nome')  # Ordena por nome
        return Servidor.objects.filter(cargo='POLICIAL PENAL').order_by('nome')  # Filtrar e ordenar por nome

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_servidores'] = Servidor.objects.count()
        # Contar os servidores com o cargo 'POLICIAL PENAL'
        context['total_policiais_penal'] = Servidor.objects.filter(cargo='POLICIAL PENAL').count()

        # Contar os servidores com status "ativo" e cargo "Policial Penal"
        context['total_servidores_ativos_policial_penal'] = Servidor.objects.filter(
            status=True, cargo='POLICIAL PENAL').count()

        # Contar os servidores com status "inativo" e cargo "Policial Penal"
        context['total_servidores_inativos_policial_penal'] = Servidor.objects.filter(
            status=False, cargo='POLICIAL PENAL').count()

        # Contar o número de servidores por gênero
        context['genero_masculino'] = Servidor.objects.filter(genero='M', cargo='POLICIAL PENAL').count()
        context['genero_feminino'] = Servidor.objects.filter(genero='F', cargo='POLICIAL PENAL').count()
        context['genero_outros'] = Servidor.objects.filter(genero='O', cargo='POLICIAL PENAL').count()

        # Labels e valores para o gráfico de pizza
        context['pie_labels'] = ['Masculino', 'Feminino', 'Outros']
        context['pie_values'] = [
            context['genero_masculino'],
            context['genero_feminino'],
            context['genero_outros']
        ]

        # Adicionar o gráfico de barras horizontal com efetivo por unidade
        efetivo_por_unidade = (
            Servidor.objects.filter(cargo='POLICIAL PENAL')
            .values('local_trabalho__nome')
            .annotate(total=Count('id'))
            .order_by('-total')
        )

        context['bar_labels'] = [item['local_trabalho__nome'] for item in efetivo_por_unidade]
        context['bar_values'] = [item['total'] for item in efetivo_por_unidade]

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

        return context


class CriarServidorView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Servidor
    form_class = ServidorForm
    template_name = 'servidor_add.html'
    success_url = reverse_lazy('servidor:recursos_humanos')

    def test_func(self):
        user = self.request.user
        # Define os grupos permitidos
        grupos_permitidos = ['Administrador', 'GerHr']
        # Retorna True se o usuário pertence a pelo menos um dos grupos
        return user.groups.filter(name__in=grupos_permitidos).exists()

        # Levanta exceção em caso de falta de permissão

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)  # Substitua '404.html' pelo nome do seu template


    def form_valid(self, form):
        # Convertendo campos de texto para maiúsculas
        servidor = form.save(commit=False)
        servidor.nome = servidor.nome.upper()
        servidor.cargo = servidor.cargo.upper()
        servidor.cargo_comissionado = servidor.cargo_comissionado.upper() if servidor.cargo_comissionado else None
        servidor.lotacao = servidor.lotacao.upper() if servidor.lotacao else None
        servidor.genero = servidor.genero.upper()
        servidor.regime = servidor.regime.upper()
        servidor.telefone = servidor.telefone if servidor.telefone else None
        servidor.email = servidor.email if servidor.email else None

        # Processamento da imagem
        if self.request.FILES:
            foto_servidor = self.request.FILES['foto_servidor']
            image = Image.open(foto_servidor)
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            max_size = (300, 300)
            image.thumbnail(max_size, Image.LANCZOS)
            buffer = BytesIO()
            image.save(buffer, format='JPEG')
            file_buffer = ContentFile(buffer.getvalue())
            servidor.foto_servidor.save(foto_servidor.name, file_buffer)

        messages.success(self.request, 'Servidor adicionado com sucesso!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Erro no Cadastro, Confira os Dados e Tente Novamente.')
        return self.render_to_response(self.get_context_data(form=form))


class ServidorEdit(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Servidor
    form_class = ServidorForm
    template_name = 'servidor_edit.html'

    def test_func(self):
        user = self.request.user
        grupos_permitidos = ['Administrador', 'GerHr']
        return user.groups.filter(name__in=grupos_permitidos).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)

    def get_success_url(self):
        return reverse_lazy('servidor:servidor_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        servidor = form.save(commit=False)
        servidor.nome = servidor.nome.upper()
        servidor.cargo = servidor.cargo.upper()
        servidor.cargo_comissionado = servidor.cargo_comissionado.upper() if servidor.cargo_comissionado else None
        servidor.lotacao = servidor.lotacao.upper() if servidor.lotacao else None
        servidor.genero = servidor.genero.upper()
        servidor.regime = servidor.regime.upper()
        servidor.usuario_responsavel = self.request.user

        # Processamento da foto do servidor
        if self.request.FILES.get('foto_servidor'):
            foto_servidor = self.request.FILES['foto_servidor']
            image = Image.open(foto_servidor)
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            max_size = (300, 300)
            image.thumbnail(max_size, Image.LANCZOS)
            buffer = BytesIO()
            image.save(buffer, format='JPEG')
            file_buffer = ContentFile(buffer.getvalue())
            servidor.foto_servidor.save(foto_servidor.name, file_buffer)

        servidor.save()

        # Processa os documentos enviados
        if self.request.FILES.getlist('documentos'):
            for arquivo in self.request.FILES.getlist('documentos'):
                # Valida o tamanho do arquivo
                if arquivo.size > 10 * 1024 * 1024:  # 10MB
                    messages.error(self.request, "O arquivo deve ter no máximo 10MB.")
                    return self.form_invalid(form)

                # Valida o tipo do arquivo
                if arquivo.content_type not in ['application/pdf', 'image/jpeg', 'image/jpg']:
                    messages.error(self.request, "Apenas arquivos PDF ou JPG são permitidos.")
                    return self.form_invalid(form)

                # Cria o documento
                Documento.objects.create(
                    servidor=servidor,
                    arquivo=arquivo,
                    descricao=self.request.POST.get('descricao', 'Documento sem descrição')
                )

        messages.success(self.request, 'Servidor e documentos atualizados com sucesso!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao editar o servidor. Verifique os dados e tente novamente.')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['historico'] = ServidorHistory.objects.filter(servidor=self.object).order_by('-data_alteracao')
        context['documento_form'] = DocumentoForm()
        context['documentos'] = Documento.objects.filter(servidor=self.object)
        # Extrai apenas os nomes dos arquivos dos documentos
        context['nomes_arquivos'] = [os.path.basename(doc.arquivo.name) for doc in context['documentos']]
        return context




class ServidorLote(LoginRequiredMixin, UserPassesTestMixin, View):
    form_class = UploadFileForm
    template_name = 'servidor_lote.html'


    def test_func(self):
        user = self.request.user
        # Define os grupos permitidos
        grupos_permitidos = ['Administrador', 'GerRh']
        # Retorna True se o usuário pertence a pelo menos um dos grupos
        return user.groups.filter(name__in=grupos_permitidos).exists()

        # Levanta exceção em caso de falta de permissão

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)  # Substitua '404.html' pelo nome do seu template


    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)

        if form.is_valid():
            arquivo_excel = request.FILES['arquivo_excel']

            # Carregar a planilha com valores calculados em vez de fórmulas
            wb = openpyxl.load_workbook(arquivo_excel, data_only=True)
            sheet = wb['servidor']

            try:
                for row in sheet.iter_rows(min_row=2, values_only=True):
                    # Verifica se a linha está em branco, ignorando-a se estiver
                    if not any(row):  # Se todos os valores da linha forem None ou vazios, pula a linha
                        continue

                    # Verifica se a matrícula ou o nome está presente, ignorando a linha se ambos estiverem ausentes
                    if not row[1] or not row[2]:
                        continue

                    # Definindo o status baseado na condição
                    status = False if row[12] == 'INATIVO' else True

                    # Atualiza ou cria um novo registro com base na matrícula
                    Servidor.objects.update_or_create(
                        matricula=str(row[0]),  # Usando matrícula como critério de identificação
                        defaults={
                            'nome': str(row[1]).upper() if row[1] else 'NAO INFORMADO',
                            'cargo': str(row[2]).upper() if row[2] else 'NAO INFORMADO',
                            'cargo_comissionado': row[3].upper() if row[3] else None,
                            'observacao': row[4] if row[4] else None,
                            'simb_cargo_comissionado': row[5] if row[5] else None,
                            'lotacao': str(row[6]).upper() if row[6] else None,
                            'local_trabalho': Unidade.objects.filter(id=row[17]).first() or Unidade.objects.get(id=1),
                            'regime': str(row[8]).upper() if row[8] else 'NAO INFORMADO',
                            'data_admissao': row[9],
                            'disposicao': str(row[10]).upper() if row[10] else None,
                            'status': status,
                            'data_nascimento': row[13],
                            'telefone': str(row[14]).upper() if row[14] else None,
                            'email': str(row[16]).upper() if row[16] else None,

                        }
                    )

                messages.success(request, 'Servidores importados com sucesso!')
            except Exception as e:
                messages.error(request, f'Ocorreu um erro ao processar o arquivo: {e}')

            return redirect('servidor:recursos_humanos')



class RelatorioRh(LoginRequiredMixin, ListView):
    model = Servidor
    template_name = "relatorio_rh.html"
    context_object_name = 'servidores'
    paginate_by = 20

    def get_queryset(self):
        queryset = Servidor.objects.all()
        query = self.request.GET.get('query')
        if query:
            queryset = queryset.filter(
                Q(nome__icontains=query) | Q(matricula__icontains=query)
            )

        cargo = self.request.GET.get('cargo')
        if cargo:
            queryset = queryset.filter(cargo=cargo)

        local_trabalho_nome = self.request.GET.get('local_trabalho')
        if local_trabalho_nome:
            # Encontre o ID correspondente ao nome
            local_trabalho_id = Unidade.objects.get(nome=local_trabalho_nome).id
            # Filtrar usando o ID
            queryset = queryset.filter(local_trabalho=local_trabalho_id)

        cargo_comissionado = self.request.GET.get('cargo_comissionado')

        # Adicione esta linha para evitar que "None" seja usado
        if cargo_comissionado == "None":
            cargo_comissionado = ""

        if cargo_comissionado:
            queryset = queryset.filter(cargo_comissionado__icontains=cargo_comissionado)

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        genero = self.request.GET.get('genero')
        if genero:
            queryset = queryset.filter(genero__icontains=genero)

        return queryset.order_by('nome')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        context['generos'] = Servidor.objects.values_list('genero', flat=True).distinct()
        context['cargos'] = Servidor.objects.values_list('cargo', flat=True).distinct()
        context['local_trabalhos'] = (Servidor.objects.values_list('local_trabalho__nome', flat=True)
                                      .distinct()
                                      .order_by('local_trabalho__nome'))
        context['cargos_comissionado'] = (
            Servidor.objects.exclude(cargo_comissionado__isnull=True)
            .exclude(cargo_comissionado__exact='')
            .values_list('cargo_comissionado', flat=True)
            .distinct()
            .order_by('cargo_comissionado')
        )
        return context


class ServidorDetail(LoginRequiredMixin, DetailView):
    model = Servidor
    template_name = "servidor_detail.html"
    context_object_name = 'servidor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Adiciona o histórico do servidor ao contexto
        context['historico'] = ServidorHistory.objects.filter(servidor=self.object).order_by('-data_alteracao')
        return context


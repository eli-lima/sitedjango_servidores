from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, CreateView, ListView, UpdateView, View
from .forms import ServidorForm, UploadFileForm
from django.urls import reverse_lazy
from django.contrib import messages
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from .models import Servidor
from django.db.models import Q
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from django.template.loader import get_template
from xhtml2pdf import pisa
import openpyxl
from django.db import IntegrityError



# Create your views here.

#Relatorios PDF

def export_to_pdf(request):
    # Recupera o valor da busca
    query = request.GET.get('query')

    # Filtra os servidores com base na busca
    if query:
        servidores = Servidor.objects.filter(
            Q(nome__icontains=query) | Q(matricula__icontains=query)
        ).order_by('nome')
    else:
        servidores = Servidor.objects.all().order_by('nome')

    # Gera o PDF
    template_path = 'servidor_pdf.html'
    context = {'servidores': servidores}

    # Renderiza o template HTML com os dados
    template = get_template(template_path)
    html = template.render(context)

    # Cria a resposta do PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="relatorio_servidores.pdf"'

    # Converte o HTML para PDF
    pisa_status = pisa.CreatePDF(html, dest=response)

    # Se houver um erro no PDF, exibe mensagem de erro
    if pisa_status.err:
        return HttpResponse('Erro ao gerar PDF', status=500)
    return response






class RecursosHumanosPage(LoginRequiredMixin, ListView):
    model = Servidor
    template_name = "servidor.html"
    context_object_name = 'servidores'
    paginate_by = 10  # Quantidade de registros por página

    def get_queryset(self):
        query = self.request.GET.get('query')
        if query:
            return Servidor.objects.filter(
                Q(nome__icontains=query) | Q(matricula__icontains=query)
            ).order_by('nome')  # Ordena por nome
        return Servidor.objects.all().order_by('nome')  # Ordena por nome



class CriarServidorView(LoginRequiredMixin, CreateView):
    model = Servidor
    form_class = ServidorForm
    template_name = 'servidor_add.html'
    success_url = reverse_lazy('servidor:recursos_humanos')  # Substitua 'servidor_list' pelo nome da URL de destino

    def form_valid(self, form):
        if self.request.FILES:
            foto_servidor = self.request.FILES['foto_servidor']

            # Abrir a imagem usando Pillow
            image = Image.open(foto_servidor)

            # Converter a imagem para RGB, se necessário
            if image.mode in ("RGBA", "P"):  # RGBA inclui transparência, P é para paletas
                image = image.convert("RGB")

            # Reduzir a resolução da imagem (ajustar conforme necessário)
            max_size = (300, 300)  # Define o tamanho máximo da imagem
            image.thumbnail(max_size, Image.LANCZOS)

            # Salvar a imagem em um buffer
            buffer = BytesIO()
            image.save(buffer, format='JPEG')

            # Criar um novo arquivo de imagem a partir do buffer
            file_buffer = ContentFile(buffer.getvalue())
            form.instance.foto_servidor.save(foto_servidor.name, file_buffer)

        # Se precisar adicionar lógica extra antes de salvar o formulário, pode ser feito aqui
        messages.success(self.request, 'Servidor adicionado com sucesso!')
        return super().form_valid(form)

    def form_invalid(self, form):
        # Isso garante que você possa ver o conteúdo do formulário mesmo se inválido
        messages.error(self.request, 'Erro no Cadastro, Confira os Dados e Tente Novamente.')
        return self.render_to_response(self.get_context_data(form=form))


class ServidorEdit(LoginRequiredMixin, UpdateView):
    model = Servidor
    form_class = ServidorForm
    template_name = 'servidor_edit.html'
    success_url = reverse_lazy('servidor:recursos_humanos')  # Redirecionar para a página de sucesso


class ServidorLote(LoginRequiredMixin, View):
    form_class = UploadFileForm
    template_name = 'servidor_lote.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)

        if form.is_valid():
            arquivo_excel = request.FILES['arquivo_excel']

            # Processar o arquivo Excel
            wb = openpyxl.load_workbook(arquivo_excel)
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
                        matricula=str(row[1]),  # Usando matrícula como critério de identificação
                        defaults={
                            'nome': str(row[2]).upper() if row[2] else 'NAO INFORMADO',
                            'cargo': str(row[3]).upper() if row[3] else 'NAO INFORMADO',
                            'local_trabalho': str(row[4]).upper() if row[4] else None,
                            'cargo_comissionado': row[5].upper() if row[5] else None,
                            'simb_cargo_comissionado': row[6] if row[6] else None,
                            'lotacao': str(row[7]).upper() if row[7] else None,
                            'genero': str(row[8]).upper() if row[8] else 'O',
                            'regime': str(row[9]).upper() if row[9] else 'NAO INFORMADO',
                            'data_admissao': row[10],
                            'status': status,
                            'data_nascimento': row[13],
                            'telefone': str(row[14]).upper() if row[14] else None,
                            'email': str(row[15]).upper() if row[15] else None,
                        }
                    )

                messages.success(request, 'Servidores importados com sucesso!')
            except Exception as e:
                messages.error(request, f'Ocorreu um erro ao processar o arquivo: {e}')

            return redirect('servidor:recursos_humanos')

        return render(request, self.template_name, {'form': form})



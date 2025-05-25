from django.shortcuts import render, redirect, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, UpdateView, View, DetailView, FormView, CreateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from servidor.models import Servidor
from .models import (Armamento, ArmamentoHistory, TipoArma, Calibre, Marca,
                     TermoAcautelamentoCounter, EstoqueMunicao,
                     MovimentacaoMunicao, LoteMunicao)
from .forms import ArmamentoForm, IncluirLoteForm, MovimentarMunicaoForm, BaixarMunicaoForm

from seappb.permissions import PermissionChecker
from django.contrib import messages
from seappb.models import Unidade
from django.utils import timezone
from django.db.models import Q
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Image, Frame
from io import BytesIO
from django.contrib.staticfiles import finders
from reportlab.lib.styles import getSampleStyleSheet
from django.db.models import Max, OuterRef, Subquery, Sum, Count
import json
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.http import JsonResponse

# Create your views here.


#Relatorios PDF
@login_required
def export_to_pdf_armamento(request):
    # Inicializa o queryset de Armamento
    armamentos = Armamento.objects.all().order_by('modelo')

    # Filtros
    query = request.GET.get('query')
    if query:
        armamentos = armamentos.filter(
            Q(modelo__icontains=query) |
            Q(numero_serie__icontains=query) |
            Q(servidor__nome__icontains=query)
        )

    modelo = request.GET.get('modelo')
    if modelo:
        armamentos = armamentos.filter(modelo=modelo)

    status = request.GET.get('status')
    if status:
        armamentos = armamentos.filter(status=status)

    local_trabalho = request.GET.get('local_trabalho')
    if local_trabalho:
        armamentos = armamentos.filter(servidor__local_trabalho=local_trabalho)

    # Gera o PDF
    template_path = 'armamento_pdf.html'
    context = {'armamentos': armamentos}

    # Renderiza o template HTML com os dados
    template = get_template(template_path)
    html = template.render(context)

    # Cria a resposta do PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="relatorio_armamentos.pdf"'

    # Converte o HTML para PDF
    pisa_status = pisa.CreatePDF(html, dest=response)

    # Se houver um erro no PDF, exibe mensagem de erro
    if pisa_status.err:
        return HttpResponse('Erro ao gerar PDF', status=500)
    return response


def generate_pdf(armamento):
    # Obter o número de controle sequencial
    numero_controle = TermoAcautelamentoCounter.get_next_number()


    # Definindo a largura e altura da página
    page_width, page_height = A4

    # Crie o buffer e o canvas
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=(page_width, page_height))

    # Definindo margens
    margin_x = 2 * cm
    margin_y = page_height - 1 * cm  # Margem superior

    # Cabeçalho com as imagens
    logo_pb_path = finders.find('images/pdf/cabecalhoPP.png')


    def resize_image(img_path, max_width, max_height):
        img = Image(img_path)
        img.drawWidth = min(img.imageWidth, max_width)
        img.drawHeight = min(img.imageHeight, max_height)
        return img

    # Ajustar o tamanho das imagens
    logo_pb = resize_image(logo_pb_path, 16.5 * cm, 2.4 * cm)


    # Posicionamento das imagens com espaçamento
    start_x = margin_x
    start_y = margin_y - logo_pb.drawHeight
    spacing = 6 * cm

    logo_pb.drawOn(c, start_x, start_y)

    # Adicionando título centralizado
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(page_width / 2, start_y - 4 * cm, "TERMO DE ACAUTELAMENTO DE ARMA DE FOGO")

    # Adicione o número de controle abaixo do título
    c.setFont("Helvetica-Bold", 12)
    c.drawString(start_x, start_y - 1 * cm, f"N° {numero_controle}")

    # Conteúdo principal do texto com quebra automática de linha
    styles = getSampleStyleSheet()
    text_style = styles["BodyText"]
    text_style.leading = 22  # Ajuste o espaçamento entre linhas aqui
    text = (
        f"Eu, {armamento.servidor.nome}, Policial Penal do Estado da Paraíba, matrícula {armamento.servidor.matricula}, "
        f"lotado(a) atualmente no(a) {armamento.servidor.local_trabalho}, RECEBI da Gerência Executiva do Sistema "
        f"Penitenciário, um (01) Armamento da Marca {armamento.marca} Modelo {armamento.modelo} Numero e Série: {armamento.numero_serie}, o qual ficará sob minha guarda e responsabilidade, "
        "ressarcindo o erário por sua perda ou extravio, independente dos procedimentos que venham a ocorrer no "
        "âmbito administrativo e criminal."
    )

    # Usando Frame e Paragraph para a quebra de linha automática
    frame = Frame(margin_x, start_y - 12 * cm, page_width - 2 * margin_x, 6 * cm, showBoundary=False)
    story = [Paragraph(text, text_style)]
    frame.addFromList(story, c)

    # Informações adicionais
    y_position = start_y - 10 * cm
    c.setFont("Helvetica", 10)

    c.drawString(margin_x, y_position - 3 * cm, "Data: ________/________/________")

    # Mantendo o mesmo estilo e alinhamento do campo "Data"
    c.setFont("Helvetica", 10)  # Certifique-se que está com a mesma fonte/tamanho que a data

    # Campos de assinatura divididos em dois blocos
    signature_y_position = start_y - 14 * cm  # Ajuste esta posição conforme necessário



    # Bloco ESQUERDO (Servidor)
    left_block_x = margin_x
    c.drawString(left_block_x, signature_y_position - 2 * cm,
                 "______________________________________")
    c.drawString(left_block_x, signature_y_position - 2.7 * cm, f"{armamento.servidor.nome} - {armamento.servidor.matricula}")


    # Bloco ESQUERDO (Gerente)
    left_block_x2 = margin_x
    c.drawString(left_block_x2, signature_y_position - 5 * cm,
                 "AUTORIZO")
    c.drawString(left_block_x2, signature_y_position - 6 * cm,
                 "______________________________________")
    c.drawString(left_block_x2, signature_y_position - 6.7 * cm,
                 "Gerente Executivo do Sistema Penitenciário")





    # Finalização do PDF
    c.showPage()
    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()


class GerarTermoPDFView(UserPassesTestMixin, LoginRequiredMixin, View):
    def test_func(self):
        return PermissionChecker.has_permission(
            user=self.request.user,
            permission_section='pagina_armaria'
        )

    def get(self, request, *args, **kwargs):
        armamento = Armamento.objects.get(pk=self.kwargs['pk'])

        if not armamento.servidor:
            messages.error(request, "Este armamento não está associado a um servidor.")
            return redirect('armaria:armamento_detail', pk=armamento.pk)

        pdf_content = generate_pdf(armamento)

        response = HttpResponse(content_type='application/pdf')
        response[
            'Content-Disposition'] = f'attachment; filename="termo_acautelamento_{armamento.servidor.matricula}.pdf"'
        response.write(pdf_content)
        return response


class Armaria(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Armamento
    template_name = "armaria.html"
    context_object_name = 'armamentos'
    paginate_by = 50

    def test_func(self):
        return PermissionChecker.has_permission(
            user=self.request.user,
            permission_section='pagina_armaria'
        )

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtros
        unidade_id = self.request.GET.get('unidade')
        servidor_id = self.request.GET.get('servidor')
        modelo = self.request.GET.get('modelo')
        numero_serie = self.request.GET.get('numero_serie')
        query = self.request.GET.get('query')

        if unidade_id and unidade_id != 'todas':
            queryset = queryset.filter(unidade__id=unidade_id)
            # Se filtro de unidade está ativo, limitar servidores dessa unidade
            if servidor_id:
                queryset = queryset.filter(servidor__id=servidor_id, servidor__unidade__id=unidade_id)
        elif servidor_id:  # Apenas filtro de servidor sem unidade
            queryset = queryset.filter(servidor__id=servidor_id)

        if modelo:
            queryset = queryset.filter(modelo__nome__icontains=modelo)
        if numero_serie:
            queryset = queryset.filter(numero_serie__icontains=numero_serie)
        if query:
            queryset = queryset.filter(
                Q(modelo__nome__icontains=query) |
                Q(tipo_arma__nome__icontains=query) |
                Q(numero_serie__icontains=query) |
                Q(servidor__nome__icontains=query) |
                Q(unidade__nome__icontains=query)
            )

        return queryset.order_by('modelo__nome')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset_filtrado = self.get_queryset()

        #total de armamentos cadastrados
        context['total_armamentos'] = Armamento.objects.count()

        unidade_id = self.request.GET.get('unidade')
        servidor_id = self.request.GET.get('servidor')

        # Filtros ativos para manter selecionado
        context['filtro_unidade'] = unidade_id
        context['filtro_servidor'] = servidor_id

        context['unidades'] = Unidade.objects.all().order_by('nome')

        # Servidores disponíveis baseados no filtro de unidade
        if unidade_id and unidade_id != 'todas':
            context['servidores'] = Servidor.objects.filter(
                local_trabalho__id=unidade_id  # Corrigido para usar local_trabalho em vez de unidade
            ).order_by('nome')
        else:
            context['servidores'] = Servidor.objects.filter(
                id__in=Armamento.objects.filter(
                    servidor__isnull=False
                ).values_list('servidor__id', flat=True).distinct()
            ).order_by('nome')

        # Totais com base no queryset filtrado
        context['total_filtrado'] = queryset_filtrado.count()
        context['total_armamento_pp'] = queryset_filtrado.filter(
            servidor__isnull=False,
            unidade__isnull=True
        ).count()
        context['total_armamento_unidade'] = queryset_filtrado.filter(
            unidade__isnull=False,
            servidor__isnull=True
        ).count()

        # Totais de munições baseados nos filtros
        estoque_municoes = EstoqueMunicao.objects.all()

        if unidade_id and unidade_id != 'todas':
            estoque_municoes = estoque_municoes.filter(unidade__id=unidade_id)
        elif servidor_id:
            estoque_municoes = estoque_municoes.filter(servidor__id=servidor_id)

        context['total_municoes'] = estoque_municoes.aggregate(
            total=Sum('quantidade')
        )['total'] or 0

        # Gráfico de armamentos por unidade (filtrado)
        armamentos_por_unidade = (
            queryset_filtrado
            .filter(unidade__isnull=False)
            .exclude(status=False)
            .values('unidade__nome')
            .annotate(total=Count('id'))
            .order_by('-total')[:10]
        )
        context['bar_labels'] = [item['unidade__nome'] for item in armamentos_por_unidade]
        context['bar_values'] = [item['total'] for item in armamentos_por_unidade]
        context['chart_title'] = "Top 10 Unidades com Mais Armamentos"

        # Gráfico de armamentos por calibre (filtrado)
        armamentos_por_calibre = (
            queryset_filtrado
            .filter(status=True)
            .values('calibre__nome')
            .annotate(total=Count('id'))
            .order_by('-total')[:10]
        )
        context['calibre_labels'] = [item['calibre__nome'] for item in armamentos_por_calibre]
        context['calibre_values'] = [item['total'] for item in armamentos_por_calibre]

        # Gráfico por tipo de arma (filtrado)
        tipos_arma = (
            queryset_filtrado
            .filter(status=True)
            .values('tipo_arma__nome')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
        context['tipo_arma_labels'] = [item['tipo_arma__nome'] for item in tipos_arma]
        context['tipo_arma_values'] = [item['total'] for item in tipos_arma]
        context['tipo_arma_cores'] = self.gerar_cores_aleatorias(len(tipos_arma))

        return context

    def gerar_cores_aleatorias(self, quantidade):
        cores = []
        for i in range(quantidade):
            hue = (i * (360 / quantidade)) % 360
            cores.append(f'hsl({hue}, 70%, 60%)')
        return cores




class ArmamentoAddView(UserPassesTestMixin, LoginRequiredMixin, FormView):
    form_class = ArmamentoForm
    template_name = 'armamento_add.html'
    success_url = reverse_lazy('armaria:armaria')  # Certifique-se que esta URL está definida

    def test_func(self):
        # Verifica se o usuário tem permissão para gestão de armamento
        return PermissionChecker.has_permission(
            user=self.request.user,
            permission_section='pagina_armaria'
        )

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Adicione aqui qualquer contexto adicional necessário
        return context

    def get_initial(self):
        """Define valores iniciais para o formulário"""
        initial = super().get_initial()
        initial['status'] = True  # Ativo por padrão
        return initial

    def form_valid(self, form):
        armamento = form.save(commit=False)
        armamento.usuario = self.request.user  # Define o usuário que está registrando

        # Garante que o status seja True (Ativo) se não foi modificado
        if 'status' not in form.changed_data:
            armamento.status = True

        armamento.save()  # Salva o armamento no banco de dados

        messages.success(self.request, 'Armamento registrado com sucesso!')
        return redirect(self.success_url)


class ArmamentoEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Armamento
    form_class = ArmamentoForm
    template_name = 'armamento_edit.html'

    def test_func(self):
        return PermissionChecker.has_permission(
            user=self.request.user,
            permission_section='pagina_armaria'
        )

    def get_success_url(self):
        messages.success(self.request, 'Armamento atualizado com sucesso!')
        return reverse_lazy('armaria:armamento_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        # Salva o estado atual antes da alteração para o histórico
        armamento = form.save(commit=False)
        original = Armamento.objects.get(pk=armamento.pk)

        # Atualiza o usuário responsável pela alteração
        armamento.usuario = self.request.user
        armamento.save()

        # Registra alterações no histórico
        self.registrar_alteracoes(original, armamento)

        return super().form_valid(form)

    def registrar_alteracoes(self, original, novo):
        changed_fields = []
        for field in original._meta.fields:
            field_name = field.name
            if getattr(original, field_name) != getattr(novo, field_name):
                changed_fields.append(field_name)

        for field in changed_fields:
            ArmamentoHistory.objects.create(
                armamento=novo,  # Note que aqui usamos 'servidor' como definido no modelo
                campo_alterado=field,
                valor_antigo=str(getattr(original, field)),
                valor_novo=str(getattr(novo, field)),
                usuario_responsavel=self.request.user
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['historico'] = ArmamentoHistory.objects.filter(
            armamento=self.object
        ).order_by('-data_alteracao')
        return context


class RelatorioArmariaView(LoginRequiredMixin, ListView):
    model = Armamento
    template_name = 'relatorio_armaria.html'
    context_object_name = 'armamentos'
    paginate_by = 40

    def get_queryset(self):
        queryset = Armamento.objects.select_related(
            'tipo_arma', 'calibre', 'marca', 'modelo', 'servidor', 'unidade'
        ).all()

        query = self.request.GET.get('query')
        if query:
            queryset = queryset.filter(
                Q(numero_serie__icontains=query) |
                Q(modelo__nome__icontains=query) |
                Q(servidor__nome__icontains=query)
            )

        tipo_arma = self.request.GET.get('tipo_arma')
        if tipo_arma:
            queryset = queryset.filter(tipo_arma__id=tipo_arma)

        calibre = self.request.GET.get('calibre')
        if calibre:
            queryset = queryset.filter(calibre__id=calibre)

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        unidade = self.request.GET.get('unidade')
        if unidade:
            queryset = queryset.filter(unidade__id=unidade)

        return queryset.order_by('numero_serie')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_obj = context['page_obj']
        paginator = page_obj.paginator

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
        context['tipos_arma'] = TipoArma.objects.all().order_by('nome')
        context['calibres'] = Calibre.objects.all().order_by('nome')
        context['unidades'] = Unidade.objects.all().order_by('nome')

        return context


class ArmamentoDetailView(UserPassesTestMixin, LoginRequiredMixin, DetailView):
    model = Armamento
    template_name = "armamento_detail.html"
    context_object_name = 'armamento'

    def test_func(self):
        return PermissionChecker.has_permission(
            user=self.request.user,
            permission_section='pagina_armaria'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['historico'] = ArmamentoHistory.objects.filter(
            armamento=self.object
        ).order_by('-data_alteracao')

        # Adiciona a URL para gerar o PDF no contexto
        context['pdf_url'] = reverse('armaria:gerar_termo', kwargs={'pk': self.object.pk})
        return context


# views municoes

class ListaMunicoesView(ListView):
    model = EstoqueMunicao
    template_name = 'lista_municoes.html'
    paginate_by = 20
    context_object_name = 'estoques'

    def get_filtered_queryset(self):
        queryset = EstoqueMunicao.objects.select_related(
            'lote', 'lote__calibre', 'unidade', 'servidor'
        )

        # Filtros
        if self.request.GET.get('calibre'):
            queryset = queryset.filter(lote__calibre_id=self.request.GET['calibre'])
        if self.request.GET.get('unidade'):
            queryset = queryset.filter(unidade_id=self.request.GET['unidade'])
        if self.request.GET.get('servidor'):
            queryset = queryset.filter(servidor_id=self.request.GET['servidor'])
        if self.request.GET.get('lote'):
            queryset = queryset.filter(lote__numero_lote__icontains=self.request.GET['lote'])

        return queryset

    def get_queryset(self):
        return self.get_filtered_queryset().order_by(
            'lote__numero_lote', 'unidade__nome', 'servidor__nome'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['calibres'] = Calibre.objects.all().order_by('nome')
        context['unidades'] = Unidade.objects.all().order_by('nome')
        context['servidores'] = Servidor.objects.all().order_by('nome')

        # Aplica os mesmos filtros no total por calibre
        filtered_queryset = self.get_filtered_queryset()
        total_por_calibre = filtered_queryset.values('lote__calibre__nome').annotate(
            total=Sum('quantidade')
        ).order_by('lote__calibre__nome')
        context['total_por_calibre'] = total_por_calibre

        return context



class IncluirLoteView(CreateView):
    form_class = IncluirLoteForm
    template_name = 'incluir_lote.html'
    success_url = reverse_lazy('armaria:lista_municoes')

    def form_valid(self, form):
        print("Entrou no form_valid")  # DEPURAÇÃO

        try:
            self.object = form.save()
            print(f"Lote salvo: {self.object}")

            unidade_armaria, created = Unidade.objects.get_or_create(nome="ARMARIA")
            print(f"Unidade ARMARIA: {unidade_armaria}, criada: {created}")

            MovimentacaoMunicao.objects.create(
                lote=self.object,
                tipo='E',
                quantidade=self.object.quantidade_inicial,
                unidade_destino=unidade_armaria,
                responsavel=self.request.user,
                documento_referencia=f"Entrada inicial - Lote {self.object.numero_lote}"
            )
            print("Movimentação criada com sucesso")

            messages.success(self.request, f"Lote {self.object.numero_lote} cadastrado com sucesso!")

            return super().form_valid(form)

        except Exception as e:
            print("Erro no form_valid:", e)
            return HttpResponse(f"Erro: {e}", status=500)


class MovimentarMunicaoView(LoginRequiredMixin, CreateView):
    form_class = MovimentarMunicaoForm
    template_name = 'movimentar_municao.html'
    success_url = reverse_lazy('armaria:lista_municoes')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['unidade_origem_id'] = self.request.GET.get('unidade')
        kwargs['lote_id'] = self.request.GET.get('lote')
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Adiciona informações úteis para o template
        if self.request.GET.get('unidade'):
            context['unidade_origem'] = Unidade.objects.get(pk=self.request.GET.get('unidade'))
        if self.request.GET.get('lote'):
            context['lote_selecionado'] = LoteMunicao.objects.get(pk=self.request.GET.get('lote'))

        return context

    def form_valid(self, form):
        form.instance.responsavel = self.request.user
        form.instance.tipo = 'T'  # Transferência

        try:
            response = super().form_valid(form)
            messages.success(self.request, "Movimentação registrada com sucesso!")
            return response
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    form.add_error(field, error)
            return self.form_invalid(form)
        except Exception as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)



class BaixarMunicaoView(LoginRequiredMixin, CreateView):
    form_class = BaixarMunicaoForm
    template_name = 'baixar_municao.html'
    success_url = reverse_lazy('armaria:lista_municoes')

    def form_valid(self, form):
        form.instance.responsavel = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Baixa de munição realizada com sucesso.')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao baixar munição. Verifique os dados e tente novamente.')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

def get_quantidade_disponivel(request):
    lote_id = request.GET.get('lote_id')
    destino_id = request.GET.get('destino_id')
    destino_type = request.GET.get('destino_type')

    quantidade = 0
    try:
        estoque = EstoqueMunicao.objects.get(
            lote_id=lote_id,
            unidade_id=destino_id if destino_type == 'unidade' else None,
            servidor_id=destino_id if destino_type == 'servidor' else None
        )
        quantidade = estoque.quantidade
    except EstoqueMunicao.DoesNotExist:
        pass

    return JsonResponse({'quantidade': quantidade})
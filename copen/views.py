from django.shortcuts import render, redirect
from django.views.generic import TemplateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import (Apreensao, TipoOcorrencia, Atendimento, Ocorrencia,
                     Custodia, Mp)
from interno.models import Interno
from .forms import (ApreensaoForm, OcorrenciaForm, AtendimentoForm,
                    Objeto, Natureza, CustodiaForm,CustodiaEditForm,
                    MpForm)
from django.views.generic import FormView, ListView
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import datetime, timedelta
from django.utils.timezone import now
from django.db.models import Count
from django.contrib.auth.mixins import UserPassesTestMixin
from .utils import calculate_bar_chart, calculate_pie_apreensao
from seappb.models import Unidade
from seappb.utils import get_periodo_12_meses, get_nome_mes, MESES_PT_BR
import json
from weasyprint import CSS
from django.http import HttpResponse
from weasyprint import HTML
import tempfile
from django.template.loader import render_to_string
from django.db.models import Q
from django.utils.dateparse import parse_date


#gerar pdf
def relatorio_resumido_apreensao(request):
    print("Iniciando relatorio_resumido_apreensao")  # Debug

    try:
        # Obter mês/ano atual
        agora = timezone.now()
        mes_atual = agora.month
        ano_atual = agora.year


        # Obter filtros com valores padrão
        mes_selecionado = int(request.GET.get('mes', mes_atual))
        ano_selecionado = int(request.GET.get('ano', ano_atual))


        # Pegar o nome do mês selecionado
        nome_mes_selecionado = MESES_PT_BR.get(mes_selecionado, f"Mês {mes_selecionado}")


        # Filtro base para todas as consultas
        base_filter = {
            'data__month': mes_selecionado,
            'data__year': ano_selecionado
        }


        # Total geral de apreensões
        total_apreensoes = Apreensao.objects.filter(**base_filter).count()


        # Quantitativo por REISP (1° a 5°)
        reisp_counts = {
            f'reisp_{i}': Apreensao.objects.filter(**base_filter, unidade__reisp=i).count()
            for i in range(1, 6)
        }


        # Dados para os gráficos
        periodo_12_meses = get_periodo_12_meses(mes_selecionado, ano_selecionado)


        # Preparar dados para o gráfico mensal
        monthly_totals = []
        monthly_labels = []

        for ano, mes, nome_mes in periodo_12_meses:
            count = Apreensao.objects.filter(data__year=ano, data__month=mes).count()
            monthly_totals.append(count)
            monthly_labels.append(f"{nome_mes[:3]}/{ano}")



        # Gráfico de pizza
        pie_labels_apreensao, pie_values_apreensao = calculate_pie_apreensao(
            mes=mes_selecionado,
            ano=ano_selecionado
        )


        # Contexto
        context = {
            'total_apreensoes': total_apreensoes,
            'reisp_1': reisp_counts['reisp_1'],
            'reisp_2': reisp_counts['reisp_2'],
            'reisp_3': reisp_counts['reisp_3'],
            'reisp_4': reisp_counts['reisp_4'],
            'reisp_5': reisp_counts['reisp_5'],
            'labels_mensais': json.dumps(monthly_labels),
            'values_mensais': json.dumps(monthly_totals),
            'pie_labels_apreensao': json.dumps(pie_labels_apreensao),
            'pie_values_apreensao': json.dumps(pie_values_apreensao),
            'meses': MESES_PT_BR,
            'anos': [str(ano) for ano in range(ano_atual - 4, ano_atual + 1)],
            'mes_selecionado': mes_selecionado,
            'nome_mes_selecionado': nome_mes_selecionado,
            'ano_selecionado': ano_selecionado,
            'nome_mes': get_nome_mes(mes_selecionado),
            'hide_nav': True,
            'is_pdf': request.GET.get('pdf', False),
            'base_url': request.build_absolute_uri('/')[:-1]
        }

        # Lógica para gerar PDF
        if request.GET.get('pdf'):

            try:
                context['is_pdf'] = True
                html_string = render_to_string('relatorios/relatorio_resumido_pdf.html', context)


                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="relatorio_apreensoes.pdf"'

                HTML(
                    string=html_string,
                    base_url=request.build_absolute_uri()
                ).write_pdf(
                    response,
                    stylesheets=[CSS(string='''
                        @page { size: A4 landscape; margin: 1.5cm; }
                        .no-print { display: none !important; }
                        .periodo-relatorio {
                            text-align: center;
                            margin-bottom: 1rem;
                            font-size: 1.1rem;
                            font-weight: bold;
                        }
                    ''')]
                )

                return response
            except Exception as e:

                raise

        # Versão HTML normal

        return render(request, 'relatorios/relatorio_resumido_apreensao.html', context)

    except Exception as e:

        raise


def gerar_pdf_generico(request, template_name, queryset, relatorio_nome, context=None, filename="relatorio.pdf"):
    """
    View genérica para gerar PDFs.
    """

    try:
        # Cria o contexto padrão
        if context is None:
            context = {}
        context['dados'] = queryset  # Passa o queryset para o template
        context['relatorio_nome'] = relatorio_nome  # Passa o queryset para o template


        # Renderiza o template HTML com os dados

        html_string = render_to_string(template_name, context)


        # Cria um objeto HTML do WeasyPrint

        html = HTML(string=html_string, base_url=request.build_absolute_uri())


        # Gera o PDF

        pdf_file = tempfile.NamedTemporaryFile(delete=False)
        html.write_pdf(target=pdf_file.name)

        # Lê o conteúdo do arquivo PDF
        pdf_file.seek(0)
        pdf = pdf_file.read()
        pdf_file.close()


        # Retorna o PDF como uma resposta HTTP
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    except Exception as e:
        print(f"ERRO em gerar_pdf_generico: {str(e)}")  # Debug
        print(f"Tipo do erro: {type(e).__name__}")  # Debug
        print(f"Template usado: {template_name}")  # Debug
        print(f"Tamanho do queryset: {len(queryset) if queryset else 0}")  # Debug
        raise



# Create your views here.

def filtrar_objetos_htmx(request):
    natureza = request.GET.get('natureza')  # Obtém o ID da natureza
    print(f'a natureza e:{natureza}')
    if natureza:
        # Filtra os objetos com base na natureza selecionada
        objetos = Objeto.objects.filter(natureza=natureza)
        print(objetos)
    else:
        # Caso não haja natureza selecionada, não retorna objetos
        objetos = []

    return render(request, 'partials/objetos_options.html', {'objetos': objetos})

def buscar_interno(request):
    query = request.GET.get('interno_nome', '').strip()

    if len(query) < 3:  # Só busca se o termo tiver mais de 3 caracteres
        internos = []
    else:
        # Busca pelo nome, CPF, prontuário ou nome da mãe
        internos = Interno.objects.filter(
            Q(nome__icontains=query) |
            Q(cpf__icontains=query) |
            Q(prontuario__icontains=query) |
            Q(nome_mae__icontains=query)
        ).order_by('nome')[:10]  # Limite de 10 resultados

    return render(request, 'partials/interno_tabela.html', {'internos': internos})


class Copen(UserPassesTestMixin, LoginRequiredMixin, TemplateView):
    template_name = "copen.html"

    def test_func(self):
        user = self.request.user
        grupos_permitidos = ['Administrador', 'Copen', 'GerGesipe']
        return user.groups.filter(name__in=grupos_permitidos).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obter o mês e o ano atuais
        hoje = now()
        mes_atual = hoje.month
        ano_atual = hoje.year

        # Filtrar os atendimentos realizados no mês atual
        lista_atendimento_mes = Atendimento.objects.filter(
            data__year=ano_atual,
            data__month=mes_atual
        )

        # Contar os atendimentos realizados no mês
        atendimento_mes = lista_atendimento_mes.count()

        context['lista_atendimento_mes'] = lista_atendimento_mes
        context['atendimento_mes'] = atendimento_mes



        # Filtrar as apreensoes realizados no mês atual
        lista_apreensao_mes = Apreensao.objects.filter(
            data__year=ano_atual,
            data__month=mes_atual
        )

        # Contar os atendimentos realizados no mês
        apreensao_mes = lista_apreensao_mes.count()

        context['lista_apreensao_mes'] = lista_apreensao_mes
        context['apreensao_mes'] = apreensao_mes

        # Filtrar os ocorrencia realizados no mês atual
        lista_ocorrencia_mes = Ocorrencia.objects.filter(
            data__year=ano_atual,
            data__month=mes_atual
        )

        # Contar os ocorrencia realizados no mês
        ocorrencia_mes = lista_ocorrencia_mes.count()


        context['lista_ocorrencia_mes'] = lista_ocorrencia_mes
        context['ocorrencia_mes'] = ocorrencia_mes

        # somar custodias ativas
        lista_custodias_ativas = Custodia.objects.filter(data_saida__isnull=True)

        custodias_ativas = lista_custodias_ativas.count()
        context['lista_custodias_ativas'] = lista_custodias_ativas
        context['custodias_ativas'] = custodias_ativas


        # Filtrar os mp realizados no mês atual
        lista_mp_mes = Mp.objects.filter(
            data_cumprimento__year=ano_atual,
            data_cumprimento__month=mes_atual
        )

        # Contar os mp realizados no mês
        mp_mes = lista_mp_mes.count()

        context['lista_mp_mes'] = lista_mp_mes
        context['mp_mes'] = mp_mes


        # graficos
        #grafico de barra mensal

        # Dicionário com os nomes dos meses
        meses = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
            7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }

        # Lista de anos disponíveis (últimos 5 anos e o atual)
        current_year = now().year
        anos = list(range(current_year - 5, current_year + 1))
        # Filtrar os registros para o mês específico

        apreensoes = Apreensao.objects.all()



        # Chamar a função para calcular os dados do gráfico
        monthly_totals_apreensao, monthly_labels_apreensao = calculate_bar_chart(apreensoes ,ano_atual, mes_atual)




        # Certifique-se de converter para `int` para usá-los em consultas e lógica
        ano_selecionado = int(ano_atual)
        mes_selecionado = int(mes_atual)


        #grafico pizza apreensoes
        # Chamar a função para calcular os dados do gráfico de pizza
        pie_labels_apreensao, pie_values_apreensao = calculate_pie_apreensao()


        # Atualizar o contexto com os filtros
        context.update({
            'monthly_totals_apreensao': monthly_totals_apreensao,
            'monthly_labels_apreensao': monthly_labels_apreensao,
            'meses': meses,
            'anos': anos,
            'ano_selecionado': ano_selecionado,
            'mes_selecionado': mes_selecionado,
            'pie_labels_apreensao': pie_labels_apreensao,
            'pie_values_apreensao': pie_values_apreensao,
        })

        # grafico pizza apreensao

        return context


class ApreensaoRelatorioView(UserPassesTestMixin, LoginRequiredMixin, ListView):
    model = Apreensao
    template_name = "relatorios/relatorio_apreensao.html"
    context_object_name = 'apreensoes'
    paginate_by = 50  # Quantidade de registros por página

    def test_func(self):
        user = self.request.user
        grupos_permitidos = ['Administrador', 'Copen', 'GerGesipe']
        return user.groups.filter(name__in=grupos_permitidos).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtro por natureza
        natureza = self.request.GET.get('natureza')
        if natureza:
            queryset = queryset.filter(natureza_id=natureza)

        # Filtro por objeto
        objeto = self.request.GET.get('objeto')
        if objeto:
            queryset = queryset.filter(objeto_id=objeto)

        # Filtro por unidade
        unidade = self.request.GET.get('unidade')
        if unidade:
            queryset = queryset.filter(unidade_id=unidade)

        # Filtro por data
        data_inicial = self.request.GET.get('dataInicial')
        data_final = self.request.GET.get('dataFinal')

        # Caso dataInicial ou dataFinal não sejam fornecidas, utilizar o mês corrente
        today = now().date()
        first_day_of_month = today.replace(day=1)
        last_day_of_month = (first_day_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        # Converter as datas para o formato correto
        if not data_inicial:
            data_inicial = first_day_of_month
        else:
            data_inicial = parse_date(data_inicial)  # Converter para objeto de data

        if not data_final:
            data_final = last_day_of_month
        else:
            data_final = parse_date(data_final)  # Converter para objeto de data

        # Aplicar o filtro de data
        if data_inicial and data_final:
            queryset = queryset.filter(data__range=[data_inicial, data_final])
        elif data_inicial:
            queryset = queryset.filter(data__gte=data_inicial)
        elif data_final:
            queryset = queryset.filter(data__lte=data_final)

        # Filtro por query (pesquisa)
        query = self.request.GET.get('query')
        if query:
            queryset = queryset.filter(descricao__icontains=query)  # Substitua 'descricao' pelo campo correto

        return queryset.order_by('data')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)


        # Adiciona as naturezas ao contexto para o filtro
        context['naturezas'] = Natureza.objects.all().order_by('nome')
        # Adiciona os objetos ao contexto para o filtro
        context['objetos'] = Objeto.objects.all().order_by('nome')
        # Adiciona as unidade ao contexto para o filtro
        context['unidades'] = Unidade.objects.all().order_by('nome')


        # Adiciona os parâmetros de filtro ao contexto para manter os valores selecionados
        context['natureza_selecionada'] = self.request.GET.get('natureza', '')
        context['objeto_selecionado'] = self.request.GET.get('objeto', '')
        context['unidade_selecionada'] = self.request.GET.get('unidade', '')
        context['dataInicial'] = self.request.GET.get('dataInicial', '')
        context['dataFinal'] = self.request.GET.get('dataFinal', '')
        context['query'] = self.request.GET.get('query', '')

        return context

    def get(self, request, *args, **kwargs):
        action = request.GET.get('action')
        queryset = self.get_queryset()
        data_inicial = self.request.GET.get('dataInicial', '')
        relatorio_nome = 'Apreensões'
        print(f'data_inicial: {data_inicial}')

        # Verifique o queryset
        print("Queryset:", queryset)
        print("Query params:", request.GET)

        if action == 'gerar_pdf_detalhado':
            print("Iniciando geração de PDF detalhado")  # Debug
            try:
                queryset = queryset
                campos = ['data', 'natureza', 'objeto', 'quantidade', 'unidade', 'descricao']
                print(f"Tamanho do queryset: {len(queryset)}")  # Debug
                print(f"Campos selecionados: {campos}")  # Debug

                return gerar_pdf_generico(
                    request,
                    template_name='relatorios/relatorio_generico_pdf.html',
                    queryset=queryset,
                    context={'campos': campos},
                    filename="relatorio_apreensoes.pdf",
                    relatorio_nome=relatorio_nome
                )
            except Exception as e:
                print(f"Erro ao gerar PDF detalhado: {str(e)}")  # Debug
                raise
        return super().get(request, *args, **kwargs)

class ApreensaoAddView(UserPassesTestMixin, LoginRequiredMixin, FormView):
    form_class = ApreensaoForm
    template_name = 'copen_apreensao_add.html'
    success_url = reverse_lazy('copen:copen')

    def test_func(self):
        user = self.request.user
        grupos_permitidos = ['Administrador', 'Copen', 'GerGesipe']
        return user.groups.filter(name__in=grupos_permitidos).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['naturezas'] = Natureza.objects.all()  # Passa as naturezas para o template
        return context

    def form_valid(self, form):
        apreensao = form.save(commit=False)
        apreensao.usuario = self.request.user
        apreensao.data_edicao = timezone.now()
        apreensao.save()
        messages.success(self.request, 'Apreensão registrada com sucesso!')
        return redirect(self.success_url)


class AtendimentoView(UserPassesTestMixin, LoginRequiredMixin, FormView):
    form_class = AtendimentoForm
    template_name = 'copen_atendimento_add.html'
    success_url = reverse_lazy('copen:copen')

    def test_func(self):
        user = self.request.user
        grupos_permitidos = ['Administrador', 'Copen', 'GerGesipe']
        return user.groups.filter(name__in=grupos_permitidos).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)

    def form_valid(self, form):
        print("\n--- INÍCIO DO form_valid ---")  # Debug
        print(f"Dados do formulário: {form.cleaned_data}")  # Debug

        try:
            atendimento = form.save(commit=False)
            print("Formulário instanciado sem salvar no banco")  # Debug

            atendimento.usuario = self.request.user
            atendimento.data_edicao = timezone.now()
            print(f"Usuário atribuído: {atendimento.usuario}")  # Debug
            print(f"Data de edição: {atendimento.data_edicao}")  # Debug

            atendimento.save()
            print("Atendimento salvo no banco com sucesso!")  # Debug
            print(f"ID do atendimento: {atendimento.id}")  # Debug

            messages.success(self.request, 'Atendimento registrado com sucesso!')
            return redirect(self.success_url)

        except Exception as e:
            print(f"ERRO ao salvar atendimento: {str(e)}")  # Debug
            print(f"Tipo de erro: {type(e).__name__}")  # Debug
            messages.error(self.request, f'Ocorreu um erro ao registrar o atendimento: {str(e)}')
            return self.form_invalid(form)

class OcorrenciaView(UserPassesTestMixin, FormView, LoginRequiredMixin):
    form_class = OcorrenciaForm
    template_name = 'copen_ocorrencia_add.html'
    success_url = reverse_lazy('copen:copen')

    def test_func(self):
        user = self.request.user
        grupos_permitidos = ['Administrador', 'Copen', 'GerGesipe']
        return user.groups.filter(name__in=grupos_permitidos).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)

    def form_valid(self, form):
        # Captura o ID do interno enviado pelo campo oculto
        interno_id = self.request.POST.get('interno_id')
        print(f"ID do interno capturado: {interno_id}")  # Debug: ID do interno

        try:
            # Verifica se o ID do interno é válido
            if interno_id:  # Verifica se o campo não está vazio
                interno = Interno.objects.get(id=interno_id)
                print(f"Interno encontrado no banco de dados: {interno}")  # Debug: Interno encontrado
            else:
                interno = None  # Define como None se o campo estiver vazio

            # Cria a ocorrência
            ocorrencia = form.save(commit=False)
            print("Instância de Ocorrencia criada a partir do formulário.")  # Debug: Instância criada

            ocorrencia.usuario = self.request.user
            print(f"Usuário associado à ocorrência: {self.request.user}")  # Debug: Usuário associado

            ocorrencia.interno = interno  # Define o interno encontrado (ou None)
            print(f"Interno associado à ocorrência: {interno}")  # Debug: Interno associado

            ocorrencia.data_edicao = timezone.now()
            ocorrencia.save()
            print("Ocorrência salva no banco de dados.")  # Debug: Ocorrência salva

            messages.success(self.request, 'Ocorrência salva com sucesso!')
            return redirect(self.success_url)

        except Interno.DoesNotExist:
            print(f"Erro: Interno com ID '{interno_id}' não encontrado.")  # Debug: Interno não encontrado
            messages.error(self.request, f"Erro: Interno não encontrado. Verifique os dados.")
            return self.form_invalid(form)

        except Exception as e:
            print(f"Erro ao salvar a ocorrência: {e}")  # Debug: Captura qualquer erro
            messages.error(self.request, "Erro ao salvar a ocorrência. Verifique os dados e tente novamente.")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        print("Preparando o contexto para o template.")  # Debug: Contexto sendo preparado
        context['tipo_objeto'] = TipoOcorrencia.objects.all()
        print(f"Tipos de ocorrência disponíveis: {context['tipo_objeto']}")  # Debug: Tipos carregados
        return context

    def form_invalid(self, form):
        print("Formulário inválido.")  # Debug: Validação falhou
        print(f"Erros do formulário: {form.errors}")  # Debug: Exibe os erros do formulário
        return super().form_invalid(form)


class CustodiaAddView(UserPassesTestMixin, FormView, LoginRequiredMixin):
    form_class = CustodiaForm
    template_name = 'copen_custodia_add.html'
    success_url = reverse_lazy('copen:copen')

    def test_func(self):
        user = self.request.user
        grupos_permitidos = ['Administrador', 'Copen', 'GerGesipe']
        return user.groups.filter(name__in=grupos_permitidos).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)

    def form_valid(self, form):
        # Captura o ID do interno enviado pelo campo oculto
        interno_id = self.request.POST.get('interno_id')
        print(f"ID do interno capturado: {interno_id}")  # Debug: ID do interno

        try:
            # Verifica se o ID do interno é válido
            interno = Interno.objects.get(id=interno_id)
            print(f"Interno encontrado no banco de dados: {interno}")  # Debug: Interno encontrado

            # Cria a ocorrência
            custodia = form.save(commit=False)
            print("Instância de custodia criada a partir do formulário.")  # Debug: Instância criada

            custodia.usuario = self.request.user
            print(f"Usuário associado à custodia: {self.request.user}")  # Debug: Usuário associado

            custodia.interno = interno  # Define o interno encontrado
            print(f"Interno associado à custodia: {interno}")  # Debug: Interno associado

            custodia.data_edicao = timezone.now()
            custodia.save()
            print("Custodia salva no banco de dados.")  # Debug: Ocorrência salva

            messages.success(self.request, 'Custódia salva com sucesso!')
            return redirect(self.success_url)

        except Interno.DoesNotExist:
            print(f"Erro: Interno com ID '{interno_id}' não encontrado.")  # Debug: Interno não encontrado
            messages.error(self.request, f"Erro: Interno não encontrado. Verifique os dados.")
            return self.form_invalid(form)

        except Exception as e:
            print(f"Erro ao salvar a ocorrência: {e}")  # Debug: Captura qualquer erro
            messages.error(self.request, "Erro ao salvar a custodia. Verifique os dados e tente novamente.")
            return self.form_invalid(form)


class CustodiaEditView(UserPassesTestMixin, UpdateView, LoginRequiredMixin):
    model = Custodia
    form_class = CustodiaEditForm
    template_name = 'copen_custodia_edit.html'
    success_url = reverse_lazy('copen:copen')

    def test_func(self):
        user = self.request.user
        grupos_permitidos = ['Administrador', 'Copen', 'GerGesipe']
        return user.groups.filter(name__in=grupos_permitidos).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)

    def form_valid(self, form):
        custodia = form.save(commit=False)
        custodia.data_edicao = now()  # Atualiza a data de edição
        custodia.save()
        messages.success(self.request, 'Data de saída salva com sucesso!')
        return redirect (self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['custodia'] = self.get_object()
        return context

    def form_invalid(self, form):
        print("Formulário inválido:", form.errors)  # Depuração
        messages.error(self.request, 'Erro ao salvar o formulário.')
        return super().form_invalid(form)


# view mandado de prisao

class MpAddView(UserPassesTestMixin, LoginRequiredMixin, FormView):
    form_class = MpForm
    template_name = 'copen_mp_add.html'
    success_url = reverse_lazy('copen:copen')

    def test_func(self):
        user = self.request.user
        grupos_permitidos = ['Administrador', 'Copen', 'GerGesipe']
        return user.groups.filter(name__in=grupos_permitidos).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)

    def form_valid(self, form):
        # Captura o ID do interno enviado pelo campo oculto
        interno_id = self.request.POST.get('interno_id')
        print(f"ID do interno capturado: {interno_id}")  # Debug: ID do interno

        try:
            # Verifica se o ID do interno é válido
            interno = Interno.objects.get(id=interno_id)
            print(f"Interno encontrado no banco de dados: {interno}")  # Debug: Interno encontrado

            # Cria a ocorrência
            mp = form.save(commit=False)
            print("Instância de mp criada a partir do formulário.")  # Debug: Instância criada

            mp.usuario = self.request.user
            print(f"Usuário associado à mp: {self.request.user}")  # Debug: Usuário associado

            mp.interno = interno  # Define o interno encontrado
            print(f"Interno associado à mp: {interno}")  # Debug: Interno associado

            mp.data_edicao = timezone.now()
            mp.save()
            print("mp salva no banco de dados.")  # Debug: Ocorrência salva

            messages.success(self.request, 'Mandado de Prisão salvo com sucesso!')
            return redirect(self.success_url)

        except Interno.DoesNotExist:
            print(f"Erro: Interno com ID '{interno_id}' não encontrado.")  # Debug: Interno não encontrado
            messages.error(self.request, f"Erro: Interno não encontrado. Verifique os dados.")
            return self.form_invalid(form)

        except Exception as e:
            print(f"Erro ao salvar a ocorrência: {e}")  # Debug: Captura qualquer erro
            messages.error(self.request, "Erro ao salvar a custodia. Verifique os dados e tente novamente.")
            return self.form_invalid(form)
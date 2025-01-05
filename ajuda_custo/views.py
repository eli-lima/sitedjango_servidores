from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, CreateView, FormView, ListView, View
from .models import Ajuda_Custo, DataMajorada, LimiteAjudaCusto, CotaAjudaCusto
from .forms import AjudaCustoForm, AdminDatasForm, LimiteAjudaCustoForm, UploadExcelRx2Form, CotaAjudaCustoForm
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Sum
from openpyxl.styles import Alignment
from django.utils.dateparse import parse_date
from django.http import HttpResponse
from openpyxl import Workbook
import pandas as pd
from servidor.models import Servidor
from django.core.paginator import Paginator
from django.contrib.auth.mixins import UserPassesTestMixin
import zipfile
from io import BytesIO
import os
from django.conf import settings
import logging
import requests
import cloudinary.uploader
from django.utils import timezone
from django.http import JsonResponse
from django.utils.timezone import now
from datetime import datetime, timedelta
from .tasks import process_batch
from celery.result import AsyncResult  # Para lidar com o status da task
from .tasks import process_excel_file  # Task Celery para processamento
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from openpyxl.styles import Alignment
from django.db.models import Sum, Case, When, IntegerField
from django.db import transaction
from seappb.models import Unidade
from .utils import (get_intervalo_mes, calcular_horas_por_unidade, get_limites_horas_por_unidade, \
        calcular_horas_a_adicionar_por_unidade, verificar_limites, get_servidor, get_registros_mes,
                    build_context)




# Create your views here.


# upload relatorios do rx2


def upload_excel_rx2(request):
    if request.method == 'POST':

        form = UploadExcelRx2Form(request.POST, request.FILES)
        if form.is_valid():

            excel_file = request.FILES['file']
            try:
                # Upload para o Cloudinary

                upload_result = cloudinary.uploader.upload(excel_file, resource_type="raw")
                cloudinary_url = upload_result['url']

                # Envia a tarefa de processamento para o Celery
                task = process_excel_file.delay(cloudinary_url)


                # Informa o usuário e redireciona para a página de status
                messages.success(request, "Arquivo enviado para o Cloudinary e processamento iniciado.")
                return redirect('ajuda_custo:status_task', task_id=task.id)

            except Exception as e:

                messages.error(request, f"Erro ao fazer upload no Cloudinary: {str(e)}")
                return redirect('ajuda_custo:upload_excel_rx2')
    else:

        form = UploadExcelRx2Form()

    return render(request, 'upload_excel_rx2.html', {'form': form})


def status_task(request, task_id):
    task = AsyncResult(task_id)


    # Verifica se a tarefa está pendente
    if task.state == 'PENDING':
        status = "Processamento pendente..."
    # Verifica se a tarefa foi concluída com sucesso
    elif task.state == 'SUCCESS':
        result = task.result
        if result['status'] == 'sucesso':
            status = "Processamento concluído com sucesso!"
        else:
            status = f"Erros encontrados: {', '.join(result['erros'])}"
    # Verifica se houve falha na tarefa
    elif task.state == 'FAILURE':
        status = f"Falha no processamento: {task.result}"
    # Para outros estados
    else:
        status = f"Processamento em andamento... Status: {task.state}"

    return render(request, 'status_task.html', {'status': status})


# def baixar zip arquivos assinados

def criar_arquivo_zip(request, queryset):
    # Cria um buffer de memória para o arquivo zip
    buffer = BytesIO()
    arquivos_adicionados = 0  # Contador para arquivos adicionados
    urls_adicionadas = set()  # Conjunto para rastrear URLs já adicionadas

    try:
        # Cria o arquivo zip em memória
        with zipfile.ZipFile(buffer, 'w') as zip_file:
            for registro in queryset:
                if registro.folha_assinada:
                    try:
                        # Obtém a URL do arquivo armazenado no Cloudinary
                        arquivo_url = registro.folha_assinada.url

                        # Verifica se a URL já foi adicionada
                        if arquivo_url in urls_adicionadas:
                            continue  # Pula para o próximo registro se já foi adicionado

                        logging.info(f"Tentando baixar arquivo: {arquivo_url}")

                        # Baixa o arquivo do Cloudinary
                        arquivo_resposta = requests.get(arquivo_url)
                        if arquivo_resposta.status_code == 200:
                            # Determina a extensão do arquivo a partir do Content-Type
                            content_type = arquivo_resposta.headers.get('Content-Type')
                            if content_type == 'application/pdf':
                                extensao = '.pdf'
                            elif content_type == 'image/jpeg':
                                extensao = '.jpeg'
                            elif content_type == 'image/jpg':
                                extensao = '.jpg'
                            else:
                                extensao = '.pdf'  # Define PDF como padrão se não houver Content-Type

                            # Configura o nome da pasta no ZIP (mês e ano)
                            pasta_nome = registro.data.strftime('%m-%Y')

                            # Configura o nome do arquivo no ZIP
                            nome_arquivo_zip = f"{registro.matricula}_{registro.data.strftime('%Y-%m')}{extensao}"

                            # Caminho completo dentro do ZIP
                            caminho_no_zip = os.path.join(pasta_nome, nome_arquivo_zip)

                            # Adiciona o arquivo ao zip
                            zip_file.writestr(caminho_no_zip, arquivo_resposta.content)
                            arquivos_adicionados += 1  # Incrementa o contador
                            urls_adicionadas.add(arquivo_url)  # Marca a URL como adicionada
                        else:
                            logging.error(f"Erro ao acessar o arquivo {registro.folha_assinada.name} no Cloudinary.")
                            messages.warning(request, f'Arquivo {registro.folha_assinada.name} não pôde ser acessado.')

                    except Exception as e:
                        logging.error(f"Erro ao adicionar arquivo {registro.folha_assinada.name} ao ZIP: {str(e)}")
                        messages.warning(request,
                                         f'Arquivo {registro.folha_assinada.name} não pôde ser adicionado ao ZIP.')

        # Log de quantos arquivos foram adicionados
        logging.info(f"Total de arquivos adicionados ao ZIP: {arquivos_adicionados}")

        # Configura o ponteiro do buffer para o início do arquivo
        buffer.seek(0)

        # Configura o nome do arquivo de download
        filename = "arquivos_assinados.zip"

        # Cria uma resposta HTTP com o tipo de conteúdo para download de arquivos ZIP
        response = HttpResponse(buffer, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response

    except Exception as e:
        logging.error(f"Erro ao criar o arquivo ZIP: {str(e)}")
        messages.error(request, 'Erro ao criar o arquivo ZIP. Tente novamente mais tarde.')
        return HttpResponse(status=500)  # Retorna um status de erro





#DEF BUSCAR NOME DE SERVIDOR


def buscar_nome_servidor(request):
    matricula = request.GET.get('matricula')
    try:
        servidor = Servidor.objects.get(matricula=matricula)
        data = {
            'nome': servidor.nome,
            'cargo': servidor.cargo
        }
        return JsonResponse(data)
    except Servidor.DoesNotExist:
        return JsonResponse({'error': 'Servidor não encontrado'}, status=404)

#DEF Download Relatorios


def exportar_excel(request):
    # Captura os parâmetros de pesquisa
    query = request.GET.get('query', '')
    data_inicial = request.GET.get('dataInicial')
    data_final = request.GET.get('dataFinal')
    unidade = request.GET.get('unidade')





    # Converte as datas em objetos datetime, se fornecidas
    data_inicial = parse_date(data_inicial) if data_inicial else None
    data_final = parse_date(data_final) if data_final else None


    # Filtrar os dados com base nos parâmetros
    queryset = Ajuda_Custo.objects.all()
    if query:
        queryset = queryset.filter(Q(nome__icontains=query) | Q(matricula__icontains=query))


    if unidade:
        queryset = queryset.filter(unidade=unidade)

    if data_inicial and data_final:
        queryset = queryset.filter(data__range=[data_inicial, data_final])
    elif data_inicial:
        queryset = queryset.filter(data__gte=data_inicial)
    elif data_final:
        queryset = queryset.filter(data__lte=data_final)



    # Processar os resultados em um dicionário
    dados_matriculas = {}
    for item in queryset:
        matricula = item.matricula
        nome = item.nome
        carga_horaria = item.carga_horaria
        data = item.data
        majorado = item.majorado



        if matricula not in dados_matriculas:
            dados_matriculas[matricula] = {'Matrícula': matricula, 'Nome': nome, 'Carga Horária Total': 0,
                                           'Horas Majoradas': 0, 'Horas Normais': 0, 'Total': 0,
                                           'Datas 12 Horas': [], 'Datas 24 Horas': [], '12h': 0, '24h': 0}

        if carga_horaria == '12 horas':
            dados_matriculas[matricula]['Datas 12 Horas'].append(pd.to_datetime(data))
            dados_matriculas[matricula]['Carga Horária Total'] += 12
            if majorado:
                dados_matriculas[matricula]['Horas Majoradas'] += 12
                dados_matriculas[matricula]['12h'] += 1
            else:
                dados_matriculas[matricula]['Horas Normais'] += 12
                dados_matriculas[matricula]['12h'] += 1

        elif carga_horaria == '24 horas':
            dados_matriculas[matricula]['Datas 24 Horas'].append(pd.to_datetime(data))
            dados_matriculas[matricula]['Carga Horária Total'] += 24
            if majorado:
                dados_matriculas[matricula]['Horas Majoradas'] += 24
                dados_matriculas[matricula]['24h'] += 1
            else:
                dados_matriculas[matricula]['Horas Normais'] += 24
                dados_matriculas[matricula]['24h'] += 1



        # Calcular o total de horas
        dados_matriculas[matricula]['Total'] = "{:07d}".format(
            int(f"{dados_matriculas[matricula]['Horas Majoradas']:03d}{dados_matriculas[matricula]['Horas Normais']:03d}")
        )



    # Criar um DataFrame com os dados processados
    df = pd.DataFrame(list(dados_matriculas.values()))

    # Exportar para Excel com openpyxl
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=ajuda_custo_resumo.xlsx'

    # Criar uma nova planilha Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Relatório Ajuda Custo"

    # Adicionar o período de datas no topo da planilha
    ws.merge_cells('A1:J1')
    ws[
        'A1'] = f"Período: {data_inicial.strftime('%d/%m/%Y')} a {data_final.strftime('%d/%m/%Y')}" if data_inicial and data_final else 'Período: Todos os Dados'

    # Adicionar os cabeçalhos das colunas
    cabecalhos = ['Matrícula', 'Nome', 'Carga Horária Total', 'Horas Majoradas', 'Horas Normais', 'Total',
                  '12h', '24h', 'Datas 12 Horas', 'Datas 24 Horas']
    ws.append(cabecalhos)

    # Função para formatar as datas em múltiplas linhas
    def formatar_datas_em_linhas(datas):
        linhas = []
        for i in range(0, len(datas), 3):  # Agrupa a cada 3 datas
            linhas.append(', '.join(datas[i:i + 3]))
        return '\n'.join(linhas)  # Junta as linhas com quebra de linha

    # Adicionar os dados do DataFrame na planilha
    for index, row in df.iterrows():
        datas_12_horas = [d.strftime('%d/%m/%Y') for d in row['Datas 12 Horas']]
        datas_24_horas = [d.strftime('%d/%m/%Y') for d in row['Datas 24 Horas']]

        # Formatar as datas em múltiplas linhas
        datas_12_horas_formatadas = formatar_datas_em_linhas(datas_12_horas)
        datas_24_horas_formatadas = formatar_datas_em_linhas(datas_24_horas)

        # Adicionar a linha formatada na planilha
        ws.append([
            row['Matrícula'], row['Nome'], row['Carga Horária Total'],
            row['Horas Majoradas'], row['Horas Normais'], row['Total'],
            row['12h'], row['24h'], datas_12_horas_formatadas, datas_24_horas_formatadas
        ])

    # Ajustar a largura das colunas ignorando a primeira linha
    for col in ws.iter_cols(min_row=2, max_col=ws.max_column):
        max_length = 0
        column_letter = col[0].column_letter  # Obtém a letra da coluna (A, B, C, etc.)
        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column_letter].width = adjusted_width

    # Ajustar o alinhamento e a altura das linhas para as colunas de datas
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=9, max_col=10):  # Colunas 9 e 10 são as de datas
        for cell in row:
            cell.alignment = Alignment(wrap_text=True)  # Permite quebra de linha dentro da célula
            num_linhas = str(cell.value).count('\n') + 1  # Conta o número de linhas dentro da célula
            ws.row_dimensions[cell.row].height = 15 * num_linhas  # Ajusta a altura da linha conforme o número de linhas

    # Ajustar o alinhamento central para todas as outras células (exceto as colunas de datas)
    for row in ws.iter_rows(min_row=2):
        for idx, cell in enumerate(row, start=1):
            if idx < 9 or idx > 10:  # Exclui as colunas 9 e 10 (as de datas)
                cell.alignment = Alignment(horizontal='left',
                                           vertical='center')  # Alinhamento horizontal e vertical central

    # Salvar a planilha no response
    wb.save(response)

    return response


def excel_detalhado(request):

    query = request.GET.get('query', '')
    data_inicial = request.GET.get('dataInicial')
    data_final = request.GET.get('dataFinal')
    unidade = request.GET.get('unidade')


    # Converte as datas em objetos datetime, se fornecidas
    data_inicial = parse_date(data_inicial) if data_inicial else None
    data_final = parse_date(data_final) if data_final else None

    # Filtrar os dados com base nos parâmetros
    queryset = Ajuda_Custo.objects.all()
    if query:
        queryset = queryset.filter(Q(nome__icontains=query) | Q(matricula__icontains=query))

    if unidade:
        queryset = queryset.filter(unidade=unidade)

    if data_inicial and data_final:
        queryset = queryset.filter(data__range=[data_inicial, data_final])
    elif data_inicial:
        queryset = queryset.filter(data__gte=data_inicial)
    elif data_final:
        queryset = queryset.filter(data__lte=data_final)

    # Processar os resultados em um dicionário
    dados = []
    for item in queryset:
        matricula = item.matricula
        unidade = item.unidade
        nome = item.nome
        cpf = ''  # Deixe a coluna de CPF em branco se não disponível
        data = item.data

        carga_horaria = item.carga_horaria

        dados.append([
            matricula,
            unidade,
            cpf,
            nome,
            data,
            carga_horaria
        ])

    # Criar uma nova planilha Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Relatório Completo Ajuda Custo"

    # Adicionar o período de datas no topo da planilha
    ws.merge_cells('A1:F1')
    ws[
        'A1'] = f"Período: {data_inicial.strftime('%d/%m/%Y')} a {data_final.strftime('%d/%m/%Y')}" if data_inicial and data_final else 'Período: Todos os Dados'

    # Adicionar os cabeçalhos das colunas
    cabecalhos = ['Matrícula', 'Unidade', 'CPF', 'Nome', 'Data', 'Carga Horária']
    ws.append(cabecalhos)

    # Adicionar os dados na planilha
    for linha in dados:
        ws.append(linha)

    # Ajustar a largura das colunas
    for col in ws.iter_cols(min_row=2, max_col=ws.max_column):
        max_length = 0
        column_letter = col[0].column_letter  # Obtém a letra da coluna (A, B, C, etc.)
        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column_letter].width = adjusted_width

    # Ajustar o alinhamento central para todas as células
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(horizontal='left', vertical='center')

    # Salvar a planilha no response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=ajuda_custo_detalhado.xlsx'
    wb.save(response)

    return response



class AjudaCusto(LoginRequiredMixin, ListView):
    model = Ajuda_Custo
    template_name = "ajuda_custo.html"
    context_object_name = 'datas'
    paginate_by = 50  # Quantidade de registros por página

    def get_queryset(self):
        user = self.request.user
        print("Usuário:", user)

        # Verificação dos grupos de usuário
        if user.groups.filter(name__in=['Administrador', 'GerGesipe']).exists():
            # Acesso completo para Administradores e GerGesipe
            queryset = Ajuda_Custo.objects.all()
            print("Usuário é Administrador ou GerGesipe")
        elif user.groups.filter(name='Gerente').exists():
            # Acesso limitado à unidade do gestor
            try:
                unidade_gestor = user.cotaajudacusto_set.first().unidade
                print("Unidade do gestor:", unidade_gestor)
                queryset = Ajuda_Custo.objects.filter(unidade=unidade_gestor)
                print("QuerySet para Gerente:", queryset)
            except AttributeError:
                # Caso o gestor não tenha uma unidade atribuída
                print("Gestor não tem unidade atribuída")
                queryset = Ajuda_Custo.objects.none()
        else:
            # Acesso limitado ao próprio usuário
            print("Usuário tem acesso limitado à própria matrícula")
            queryset = Ajuda_Custo.objects.filter(matricula=user.matricula)

        # Captura os valores de ano e mês do formulário de filtro
        ano_selecionado = self.request.GET.get('ano', timezone.now().year)
        mes_selecionado = self.request.GET.get('mes', timezone.now().month)
        print("Ano selecionado:", ano_selecionado)
        print("Mês selecionado:", mes_selecionado)

        # Certifique-se de converter para int
        ano_selecionado = int(ano_selecionado)
        mes_selecionado = int(mes_selecionado)

        # Filtrar por ano e mês
        queryset = queryset.filter(data__year=ano_selecionado, data__month=mes_selecionado)
        print("QuerySet após filtro de ano e mês:", queryset)

        # Filtrar por data (mês atual)
        today = now().date()
        first_day_of_month = today.replace(day=1)
        last_day_of_month = (first_day_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        print("Primeiro dia do mês:", first_day_of_month)
        print("Último dia do mês:", last_day_of_month)

        # Aplicar filtro de data
        data_inicial = first_day_of_month
        data_final = last_day_of_month
        queryset = queryset.filter(data__range=[data_inicial, data_final])
        print("QuerySet após filtro de data:", queryset)

        return queryset.order_by('nome')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Paginação personalizada
        page_obj = context['page_obj']
        paginator = page_obj.paginator
        page_range = paginator.page_range

        print("Page Obj:", page_obj)
        print("Paginator:", paginator)
        print("Page Range:", page_range)

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
        print("Page Range Context:", context['page_range'])

        # Dicionário com os nomes dos meses
        meses = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
            7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }

        # Lista de anos disponíveis (últimos 5 anos e o atual)
        current_year = now().year
        anos = list(range(current_year - 5, current_year + 1))

        # Captura os valores de ano e mês enviados pelo formulário de filtro
        ano_selecionado = self.request.GET.get('ano', timezone.now().year)
        mes_selecionado = self.request.GET.get('mes', timezone.now().month)
        print("Ano e mês selecionados no contexto:", ano_selecionado, mes_selecionado)

        # Certifique-se de converter para `int` para usá-los em consultas e lógica
        ano_selecionado = int(ano_selecionado)
        mes_selecionado = int(mes_selecionado)

        # Atualizar o contexto com os filtros
        context.update({
            'meses': meses,
            'anos': anos,
            'ano_selecionado': ano_selecionado,
            'mes_selecionado': mes_selecionado,
        })

        # Construir o restante do contexto com os filtros aplicados
        return build_context(self.request, context, ano_selecionado, mes_selecionado)


class RelatorioAjudaCusto(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Ajuda_Custo
    template_name = "relatorio_ajuda_custo.html"
    context_object_name = 'datas'
    paginate_by = 50  # Quantidade de registros por página

    def test_func(self):
        user = self.request.user
        grupos_permitidos = ['Administrador', 'GerGesipe']
        return user.groups.filter(name__in=grupos_permitidos).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)

    def get_queryset(self):
        query = self.request.GET.get('query', '')
        data_inicial = self.request.GET.get('dataInicial')
        data_final = self.request.GET.get('dataFinal')

        # Caso dataInicial ou dataFinal não sejam fornecidas, utilizar o mês corrente
        today = now().date()
        first_day_of_month = today.replace(day=1)
        last_day_of_month = (first_day_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        # Garantir que as datas estejam no formato de string antes de usar parse_date
        if not data_inicial:
            data_inicial = first_day_of_month
        else:
            data_inicial = parse_date(data_inicial)  # Converter para objeto de data

        if not data_final:
            data_final = last_day_of_month
        else:
            data_final = parse_date(data_final)  # Converter para objeto de data

        queryset = Ajuda_Custo.objects.all()

        if query:
            queryset = queryset.filter(
                Q(nome__icontains=query) | Q(matricula__icontains=query)
            )

        #filtro por unidade:

        unidade = self.request.GET.get('unidade')
        if unidade:
            queryset = queryset.filter(unidade=unidade)


        # Aplicar filtro de data apenas se as datas forem válidas
        if data_inicial and data_final:
            queryset = queryset.filter(data__range=[data_inicial, data_final])
        elif data_inicial:
            queryset = queryset.filter(data__gte=data_inicial)
        elif data_final:
            queryset = queryset.filter(data__lte=data_final)

        return queryset.order_by('nome')


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

        # Garantir que as datas estejam no formato correto (YYYY-MM-DD)
        today = now().date()
        first_day_of_month = today.replace(day=1)
        last_day_of_month = (first_day_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        data_inicial = self.request.GET.get('dataInicial', first_day_of_month)
        data_final = self.request.GET.get('dataFinal', last_day_of_month)

        # Certifique-se de que as datas estejam formatadas corretamente (YYYY-MM-DD)
        if isinstance(data_inicial, str):
            data_inicial = parse_date(data_inicial)  # Se for string, converter para data
        if isinstance(data_final, str):
            data_final = parse_date(data_final)  # Se for string, converter para data

        context['query'] = self.request.GET.get('query', '')
        context['dataInicial'] = data_inicial.strftime('%Y-%m-%d') if data_inicial else ''
        context['dataFinal'] = data_final.strftime('%Y-%m-%d') if data_final else ''
        # Ajuste aqui: mudando 'unidade' para 'unidades'
        context['unidades'] = Ajuda_Custo.objects.values_list('unidade', flat=True).distinct()

        return context

    def get(self, request, *args, **kwargs):
        action = request.GET.get('action')
        if action == 'export_excel':
            return exportar_excel(request)
        elif action == 'excel_detalhado':
            return excel_detalhado(request)
        elif action == 'arquivos_assinados':
            queryset = self.get_queryset()
            return criar_arquivo_zip(request, queryset)
        return super().get(request, *args, **kwargs)


class AjudaCustoAdicionar(LoginRequiredMixin, FormView):
    model = Ajuda_Custo
    form_class = AjudaCustoForm
    template_name = 'ajuda_custo_add.html'
    success_url = reverse_lazy('ajuda_custo:ajuda_custo')

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        from django.contrib import messages

        if form.is_valid():
            mes = request.POST.get('mes')
            ano = request.POST.get('ano')
            dias = request.POST.getlist('dia')
            unidades = request.POST.getlist('unidade')
            cargas_horarias = request.POST.getlist('carga_horaria')


            print("Dados recebidos do formulário:")
            print(f"Mes: {mes}, Ano: {ano}, Dias: {dias}, Unidades: {unidades}, Cargas Horárias: {cargas_horarias}")

            try:
                servidor = get_servidor(request)
                print(f"Servidor encontrado: {servidor}")
                nome_servidor = servidor.nome

                inicio_do_mes, fim_do_mes = get_intervalo_mes(int(mes), int(ano))
                print(f"Início do mês: {inicio_do_mes}, Fim do mês: {fim_do_mes}")

                registros_mes = get_registros_mes(servidor, inicio_do_mes, fim_do_mes)
                print(f"Registros do mês encontrados: {registros_mes.count()}")

                horas_por_unidade, horas_totais = calcular_horas_por_unidade(registros_mes)
                print("Horas por unidade no mês:", horas_por_unidade)
                print(f"Horas totais no mês: {horas_totais}")

                limites_horas_por_unidade = get_limites_horas_por_unidade(servidor)
                print("Limites de horas por unidade:", limites_horas_por_unidade)

                horas_a_adicionar_por_unidade = calcular_horas_a_adicionar_por_unidade(unidades, cargas_horarias)
                print("Horas a adicionar por unidade:", horas_a_adicionar_por_unidade)

                if not verificar_limites(horas_totais, horas_a_adicionar_por_unidade, horas_por_unidade,
                                         limites_horas_por_unidade, request):
                    return self.form_invalid(form)

                ajuda_custo_instances, error_messages = self.processar_datas(dias, unidades, cargas_horarias, servidor,
                                                                             nome_servidor, mes, ano, request)
                self.exibir_mensagens(error_messages)
                self.enviar_email(ajuda_custo_instances, error_messages)

                # Verificação e atualização da folha assinada
                novo_arquivo = form.cleaned_data.get('folha_assinada')
                if novo_arquivo:
                    ano_int = int(ano)
                    mes_int = int(mes)
                    registros_existentes = Ajuda_Custo.objects.filter(
                        matricula=servidor.matricula,
                        data__year=ano_int,
                        data__month=mes_int
                    )

                    if registros_existentes.exists():
                        for registro in registros_existentes:
                            arquivo_antigo = registro.folha_assinada
                            if arquivo_antigo:
                                try:
                                    arquivo_antigo.delete(save=False)
                                except Exception as e:
                                    messages.error(self.request, f'Erro ao excluir o arquivo antigo: {e}')

                        primeiro_registro = registros_existentes.first()
                        if primeiro_registro.folha_assinada != novo_arquivo:
                            primeiro_registro.folha_assinada = novo_arquivo
                            primeiro_registro.save()

                        for registro in registros_existentes:
                            registro.folha_assinada = primeiro_registro.folha_assinada
                            try:
                                registro.save()
                            except Exception as e:
                                messages.error(self.request, f'Erro ao salvar registro {registro.id}: {e}')

                    return redirect(self.success_url)

            except Exception as e:
                print(f"Erro interno: {e}")
                from django.contrib import messages
                messages.error(request, 'Ocorreu um erro interno. Tente novamente mais tarde.')
                return self.form_invalid(form)

        return self.form_invalid(form)

    @staticmethod
    def processar_datas(dias, unidades, cargas_horarias, servidor, nome_servidor, mes, ano, request):

        error_messages = []
        ajuda_custo_instances = []

        with transaction.atomic():
            for dia, unidade_nome, carga_horaria in zip(dias, unidades, cargas_horarias):
                try:
                    data_completa = datetime.strptime(f"{dia}/{mes}/{ano}", "%d/%m/%Y").date()
                    print(f"Processando data: {data_completa}")
                    horas_a_adicionar = int(carga_horaria.strip().replace(' horas', ''))
                    print(f"Horas a adicionar: {horas_a_adicionar}")

                    if Ajuda_Custo.objects.filter(matricula=servidor.matricula, data=data_completa).exists():
                        error_messages.append(f'O servidor já possui uma entrada para {dia}/{mes}/{ano}.')
                        print(f"Data duplicada detectada: {data_completa}")
                        continue

                    carga_horaria_final = f"{horas_a_adicionar} horas"
                    ajuda_custo = Ajuda_Custo(
                        matricula=servidor.matricula,
                        nome=nome_servidor,
                        data=data_completa,
                        unidade=unidade_nome,
                        carga_horaria=carga_horaria_final,
                        majorado=DataMajorada.objects.filter(data=data_completa).exists()
                    )
                    ajuda_custo.save()
                    ajuda_custo_instances.append(ajuda_custo)
                    print(f"Registro salvo: {ajuda_custo}")

                except Exception as e:
                    print(f"Erro ao processar data {dia}/{mes}/{ano}: {e}")
                    error_messages.append(f'Ocorreu um erro ao processar a data {dia}/{mes}/{ano}.')

        return ajuda_custo_instances, error_messages

    def exibir_mensagens(self, error_messages):

        for message in error_messages:
            messages.error(self.request, message)
        if not error_messages:
            messages.success(self.request, 'Datas adicionadas com sucesso!')
        else:
            messages.warning(self.request,
                             'Processamento concluído com algumas falhas. Verifique as mensagens de erro.')

    def enviar_email(self, ajuda_custo_instances, error_messages):
        email_destinatario = self.request.user.email

        assunto = 'Confirmação de Datas Marcadas'
        contexto = {'ajuda_custo_list': ajuda_custo_instances, 'servidor': self.request.user.nome_completo,
                    'matricula': self.request.user.matricula, 'error_messages': error_messages}
        corpo_email = render_to_string('email_datasmarcadas.html', contexto)
        email = EmailMessage(assunto, corpo_email, settings.EMAIL_HOST_USER, [email_destinatario], )
        email.content_subtype = 'html'
        email.send()
        print('email enviado com sucesso')


class AdminCadastrar(LoginRequiredMixin, UserPassesTestMixin, FormView):
    model = Ajuda_Custo
    form_class = AdminDatasForm
    template_name = 'admin_cadastrar.html'
    success_url = reverse_lazy('ajuda_custo:admin_cadastrar')

    def test_func(self):
        user = self.request.user
        # Define os grupos permitidos
        grupos_permitidos = ['Administrador', 'GerGesipe']
        # Retorna True se o usuário pertence a pelo menos um dos grupos
        return user.groups.filter(name__in=grupos_permitidos).exists()

        # Levanta exceção em caso de falta de permissão

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)  # Substitua '404.html' pelo nome do seu template

    def form_valid(self, form):
        mes = form.cleaned_data['mes']
        ano = form.cleaned_data['ano']
        unidade = form.cleaned_data['unidade']
        dias_12h = form.cleaned_data['dias_12h']
        dias_24h = form.cleaned_data['dias_24h']

        dias_12h_list = [dia.strip() for dia in dias_12h.split(',') if dia.strip()]
        dias_24h_list = [dia.strip() for dia in dias_24h.split(',') if dia.strip()]

        # Pegando a matrícula do campo do formulário (presumindo que o campo seja 'matricula')
        matricula = self.request.POST.get('matricula')

        # Obtém o servidor com base na matrícula fornecida no formulário
        try:
            servidor = Servidor.objects.get(matricula=matricula)
        except Servidor.DoesNotExist:
            messages.error(self.request, 'Erro: Servidor não encontrado.')
            return redirect(self.success_url)

        mes_int = int(mes)
        ano_int = int(ano)

        # Verifica o total de horas mensais antes de adicionar cada registro
        for dia in dias_12h_list + dias_24h_list:
            try:
                data_completa = datetime.strptime(f"{dia}/{mes}/{ano}", "%d/%m/%Y").date()

                # Verifique se o servidor já marcou essa data, independentemente da carga horária
                if Ajuda_Custo.objects.filter(matricula=servidor.matricula, data=data_completa).exists():
                    messages.error(self.request, f'O servidor já possui uma entrada para {dia}/{mes}/{ano}.')
                    return redirect(self.success_url)

                inicio_do_mes = data_completa.replace(day=1)
                fim_do_mes = (inicio_do_mes + timedelta(days=31)).replace(day=1) - timedelta(days=1)

                registros_mes = Ajuda_Custo.objects.filter(
                    matricula=servidor.matricula,
                    data__range=[inicio_do_mes, fim_do_mes]
                )

                total_horas_mes = 0
                for registro in registros_mes:
                    if registro.carga_horaria == '12 horas':
                        total_horas_mes += 12
                    elif registro.carga_horaria == '24 horas':
                        total_horas_mes += 24

                horas_a_adicionar = 12 if dia in dias_12h_list else 24

                if total_horas_mes + horas_a_adicionar > 192:
                    messages.error(self.request, f'Limite de 192 horas mensais excedido para {dia}/{mes}/{ano}.')
                    return redirect(self.success_url)

                majorado = DataMajorada.objects.filter(data=data_completa).exists()

                ajuda_custo = Ajuda_Custo(
                    matricula=servidor.matricula,
                    nome=servidor.nome,
                    data=data_completa,
                    unidade=unidade,
                    carga_horaria='12 horas' if dia in dias_12h_list else '24 horas',
                    majorado=majorado
                )
                ajuda_custo.save()

            except ValueError:
                messages.error(self.request, f'Erro: Data inválida - {dia}/{mes}/{ano}')
                return redirect(self.success_url)

        messages.success(self.request, 'Datas adicionadas com sucesso!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Erro no Cadastro, Confira os Dados e Tente Novamente.')
        return super().form_invalid(form)


from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.contrib import messages
from django.db.models import Q
from .forms import LimiteAjudaCustoForm, CotaAjudaCustoForm
from .models import LimiteAjudaCusto, CotaAjudaCusto, Unidade

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import FormView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator

from .forms import LimiteAjudaCustoForm, CotaAjudaCustoForm
from .models import LimiteAjudaCusto, CotaAjudaCusto, Unidade

class HorasLimite(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'horas_limite.html'
    success_url = reverse_lazy('ajuda_custo:horas_limite')

    def test_func(self):
        user = self.request.user
        grupos_permitidos = ['Administrador', 'GerGesipe']
        has_permission = user.groups.filter(name__in=grupos_permitidos).exists()
        print(f"Usuário: {user}, Grupos: {user.groups.all()}, Permissão: {has_permission}")
        return has_permission

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)

    def get_form_class(self):
        if self.request.method == 'POST':
            if 'servidor' in self.request.POST:
                return LimiteAjudaCustoForm
            else:
                return CotaAjudaCustoForm
        return LimiteAjudaCustoForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            query = self.request.GET.get('query', '')
            unidade = self.request.GET.get('unidade', '')
            print(f"Query: {query}, Unidade: {unidade}")

            # Paginação para LimiteAjudaCusto (aba Individual)
            filtros_cargas = Q()
            if query:
                filtros_cargas &= Q(servidor__nome__icontains=query) | Q(servidor__matricula__icontains=query)
            if unidade:
                filtros_cargas &= Q(unidade__nome=unidade)

            cargas = LimiteAjudaCusto.objects.filter(filtros_cargas).order_by('id')
            paginator_cargas = Paginator(cargas, 10)
            page_number_cargas = self.request.GET.get('page_cargas')
            page_obj_cargas = paginator_cargas.get_page(page_number_cargas)
            print("Page Obj Cargas:", page_obj_cargas)

            # Paginação para CotaAjudaCusto (aba Gerências)
            filtros_cota = Q()
            if query:
                filtros_cota &= Q(gestor__username__icontains=query) | Q(gestor__first_name__icontains=query) | Q(gestor__last_name__icontains=query)
            if unidade:
                filtros_cota &= Q(unidade__nome=unidade)

            cotas = CotaAjudaCusto.objects.filter(filtros_cota).order_by('id')
            paginator_cotas = Paginator(cotas, 10)
            page_number_cotas = self.request.GET.get('page_cotas')
            page_obj_cotas = paginator_cotas.get_page(page_number_cotas)
            print("Page Obj Cotas:", page_obj_cotas)

            # Adiciona os dados ao contexto
            context.update({
                'unidades': Unidade.objects.values_list('nome', flat=True),
                'carga_horaria': page_obj_cargas,
                'cota_horaria': page_obj_cotas,
                'page_obj_cargas': page_obj_cargas,
                'page_obj_cotas': page_obj_cotas,
                'query': query,
                'unidade': unidade,
            })

            # Adiciona os formulários para carga horária individual e por gerências
            context['form_individual'] = LimiteAjudaCustoForm()
            context['form_gerencia'] = CotaAjudaCustoForm()
            print("Context:", context)

        except Exception as e:
            print(f"Erro ao gerar o contexto: {e}")
            messages.error(self.request, f"Erro ao carregar a página: {e}")
            context['erro'] = str(e)

        return context

    def post(self, request, *args, **kwargs):
        if 'servidor' in request.POST:
            form = LimiteAjudaCustoForm(request.POST)
            if form.is_valid():
                return self.form_individual_valid(form)
            else:
                return self.form_invalid(form)
        else:
            form = CotaAjudaCustoForm(request.POST)
            if form.is_valid():
                return self.form_gerencia_valid(form)
            else:
                return self.form_invalid(form)

    def form_individual_valid(self, form):
        servidor = form.cleaned_data['servidor']
        unidade = form.cleaned_data['unidade']
        limite_horas = form.cleaned_data['limite_horas']

        # Verifica se a carga horária excede 192 horas
        if limite_horas > 192:
            messages.error(self.request, "A carga horária não pode ultrapassar 192 horas.")
            return self.form_invalid(form)

        LimiteAjudaCusto.objects.update_or_create(
            servidor=servidor,
            unidade=unidade,
            defaults={'limite_horas': limite_horas}
        )

        messages.success(self.request, 'Limite de horas atualizado com sucesso!')
        return redirect(self.success_url)

    def form_gerencia_valid(self, form):
        gestor = form.cleaned_data['gestor']
        unidade = form.cleaned_data['unidade']
        cota_ajudacusto = form.cleaned_data['cota_ajudacusto']

        CotaAjudaCusto.objects.update_or_create(
            gestor=gestor,
            unidade=unidade,
            defaults={'cota_ajudacusto': cota_ajudacusto}
        )

        messages.success(self.request, 'Cota de ajuda de custo atualizada com sucesso!')
        return redirect(self.success_url)


class CargaHorariaGerente(LoginRequiredMixin, UserPassesTestMixin, FormView):
    model = LimiteAjudaCusto
    form_class = LimiteAjudaCustoForm
    template_name = 'cargahoraria_gerente.html'
    success_url = reverse_lazy('ajuda_custo:cargahoraria_gerente')

    # Verifica se o usuário pertence a determinados grupos
    def test_func(self):
        user = self.request.user
        # Define os grupos permitidos
        grupos_permitidos = ['Administrador', 'Gerente', 'GerGesipe']
        return user.groups.filter(name__in=grupos_permitidos).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)

    def form_valid(self, form):
        gestor = self.request.user
        unidade = form.cleaned_data['unidade']
        limite_horas = form.cleaned_data['limite_horas']
        servidor = form.cleaned_data['servidor']

        # Verifica se a carga horária excede 192 horas
        if limite_horas > 192:
            messages.error(self.request, "A carga horária não pode ultrapassar 192 horas.")
            return self.form_invalid(form)

        # Verifique a cota disponível do gerente
        cota = CotaAjudaCusto.objects.get(gestor=gestor, unidade=unidade)
        if limite_horas > cota.carga_horaria_disponivel:
            messages.error(self.request, f"Você não pode distribuir mais que {cota.carga_horaria_disponivel} horas.")
            return self.form_invalid(form)

        # Atualize ou crie o limite de horas
        LimiteAjudaCusto.objects.update_or_create(
            servidor=servidor,
            unidade=unidade,
            defaults={'limite_horas': limite_horas}
        )

        # Atualize a cota disponível
        cota.save()

        messages.success(self.request, 'Carga horária distribuída com sucesso!')
        return redirect(self.success_url)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Adicione a unidade baseada no gestor
        kwargs['initial'] = {'unidade': self.request.user.cotaajudacusto_set.first().unidade}
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Torne o campo unidade somente leitura
        form.fields['unidade'].disabled = True
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtenha o valor da consulta de pesquisa, se houver
        query = self.request.GET.get('query', '')
        unidade_nome = self.request.GET.get('unidade', '')
        context['cota_total'] = self.request.user.cotaajudacusto_set.first().carga_horaria_total
        context['cota_disponivel'] = self.request.user.cotaajudacusto_set.first().carga_horaria_disponivel

        # Filtra por nome, matrícula e unidade, se houver uma consulta
        filtros = Q()
        if query:
            filtros &= Q(servidor__nome__icontains=query) | Q(servidor__matricula__icontains=query)

        # Valida o nome da unidade antes de aplicar na query
        if unidade_nome:
            try:
                unidade = Unidade.objects.get(nome=unidade_nome)
                filtros &= Q(unidade=unidade)
            except Unidade.DoesNotExist:
                messages.error(self.request, f"Unidade '{unidade_nome}' não encontrada.")
                filtros &= Q(pk__isnull=True)  # Retorna nenhum resultado

        # Filtra as cargas horárias com base no gestor logado
        # Aqui você verifica que a unidade da cota do gestor seja a mesma que estamos buscando
        cargas = LimiteAjudaCusto.objects.filter(filtros, unidade__cotaajudacusto__gestor=self.request.user)

        # Limita a carga horária máxima a 192 horas
        cargas = cargas.filter(limite_horas__lte=192)

        # Adiciona a paginação
        paginator = Paginator(cargas, 20)  # Mostra 20 registros por página
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Adiciona os dados ao contexto
        context['unidades'] = Unidade.objects.values_list('nome', flat=True)
        context['carga_horaria'] = page_obj
        context['page_obj'] = page_obj
        context['query'] = query
        context['unidade'] = unidade_nome

        return context


def excluir_cota(request, pk):
    cota = get_object_or_404(CotaAjudaCusto, pk=pk)
    cota.delete()
    messages.success(request, 'Cota de horas excluído com sucesso!')
    return redirect('ajuda_custo:horas_limite')  # Redirecionamento padrão


def excluir_limite(request, pk):
    limite = get_object_or_404(LimiteAjudaCusto, pk=pk)
    unidade = limite.unidade
    limite_horas = limite.limite_horas
    limite.delete()

    # Atualize a carga horária disponível da gerência correspondente
    cota = CotaAjudaCusto.objects.filter(unidade=unidade).first()
    if cota:
        cota.carga_horaria_disponivel += limite_horas
        cota.save()

    messages.success(request, 'Limite de horas excluído com sucesso!')

    # Redireciona com base no grupo do usuário
    if request.user.groups.filter(name='Gerente').exists():
        return redirect('ajuda_custo:cargahoraria_gerente')
    elif request.user.groups.filter(name='Administrador').exists():
        return redirect('ajuda_custo:horas_limite')
    else:
        return redirect('ajuda_custo:horas_limite')  # Redirecionamento padrão


class VerificarCargaHoraria(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Ajuda_Custo
    template_name = "verificar_carga_horaria.html"
    context_object_name = "dados"
    paginate_by = 50  # Paginação

    def test_func(self):
        user = self.request.user
        grupos_permitidos = ["Administrador", "GerGesipe"]
        return user.groups.filter(name__in=grupos_permitidos).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, "403.html", status=403)

    def get_queryset(self):
        # Obter o mês, ano e termo de busca
        mes = self.request.GET.get("mes")
        ano = self.request.GET.get("ano")
        query = self.request.GET.get("query", "").strip()  # Remover espaços extras

        # Filtro inicial: por mês e ano
        queryset = Ajuda_Custo.objects.all()

        if mes and ano:
            queryset = queryset.filter(data__year=ano, data__month=mes)

        # Filtro adicional: por nome
        if query:
            queryset = queryset.filter(nome__icontains=query)

        # Ordenar explicitamente por nome ou outro campo relevante
        return queryset.order_by("nome")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obter parâmetros do filtro
        mes = self.request.GET.get("mes")
        ano = self.request.GET.get("ano")
        query = self.request.GET.get("query", "").strip()

        today = now().date()

        if not mes:
            mes = today.month
        if not ano:
            ano = today.year

        # Dados agregados por servidor
        dados_ajuda_custo = (
            Ajuda_Custo.objects.filter(data__year=ano, data__month=mes)
            .values("matricula", "nome")
            .annotate(
                total_horas=Sum(
                    Case(
                        When(carga_horaria="12 horas", then=12),
                        When(carga_horaria="24 horas", then=24),
                        default=0,
                        output_field=IntegerField(),
                    )
                )
            )
        )

        # Filtro por nome (query)
        if query:
            dados_ajuda_custo = dados_ajuda_custo.filter(nome__icontains=query)

        # Lógica de limites, erros e ordenação (como antes)
        dados_com_limites = []
        total_erros = 0
        for ajuda in dados_ajuda_custo:
            matricula = ajuda["matricula"]
            limite = (
                LimiteAjudaCusto.objects.filter(servidor__matricula=matricula)
                .values("limite_horas")
                .first()
            )
            ajuda["limite_horas"] = limite["limite_horas"] if limite else None

            # Determinar se há erro
            erro = False
            if ajuda["total_horas"] > 192 or (
                    ajuda["limite_horas"] is not None
                    and ajuda["total_horas"] > ajuda["limite_horas"]
            ):
                erro = True
                total_erros += 1
            ajuda["erro"] = erro

            # Adicionar prioridade de ordenação
            if ajuda["total_horas"] > 192:
                prioridade = 1
            elif ajuda["limite_horas"] is not None:
                prioridade = 2
            else:
                prioridade = 3

            ajuda["prioridade"] = prioridade
            dados_com_limites.append(ajuda)

        # Ordenar por prioridade e erro
        dados_com_limites.sort(key=lambda x: (x["prioridade"], not x["erro"]))

        # Mapeamento de meses
        meses_nomes = {
            1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio",
            6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro",
            11: "Novembro", 12: "Dezembro"
        }

        context["dados"] = dados_com_limites
        context["mes"] = int(mes)
        context["ano"] = int(ano)
        context["query"] = query  # Adicionar o termo de busca ao contexto
        context["meses"] = [(num, nome) for num, nome in meses_nomes.items()]
        context["anos"] = range(today.year - 5, today.year + 1)  # Últimos 5 anos
        context["mes_atual_nome"] = meses_nomes[int(mes)]
        context["total_erros"] = total_erros

        return context

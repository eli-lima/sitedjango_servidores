from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, CreateView, FormView, ListView, View
from .models import Ajuda_Custo, DataMajorada, LimiteAjudaCusto
from .forms import AjudaCustoForm, AdminDatasForm, LimiteAjudaCustoForm, UploadExcelRx2Form
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Sum
from openpyxl.styles import Alignment
from django.utils.dateparse import parse_date
from django.http import HttpResponse
from openpyxl import Workbook
import pandas as pd
from django.http import JsonResponse
from servidor.models import Servidor
from django.core.paginator import Paginator
from django.contrib.auth.mixins import UserPassesTestMixin
import zipfile
from io import BytesIO
import os
from django.conf import settings
import logging
import requests
import re
from dateutil import parser  # Isso ajudará a lidar com diferentes formatos de data
from django.utils.timezone import now
from datetime import datetime, timedelta




# Create your views here.
#upload relatorios do rx2


def upload_excel_rx2(request):
    if request.method == 'POST':
        form = UploadExcelRx2Form(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['file']
            try:
                # Ler o arquivo Excel
                df = pd.read_excel(excel_file)

                registros_inseridos = False

                # Iterar pelas linhas da planilha
                for _, row in df.iterrows():
                    # Verificar se a matrícula existe e não é nula
                    matricula_raw = row['Matrícula']
                    if pd.isnull(matricula_raw):
                        messages.error(request, "Erro: Matrícula vazia encontrada.")
                        continue

                    # Convertendo a matrícula para string e removendo caracteres não numéricos
                    matricula = re.sub(r'\D', '', str(matricula_raw)).lstrip('0')

                    unidade = row['Unidade']
                    nome = row['Nome']
                    data = row['Data']
                    carga_horaria = row['Carga Horaria']

                    # Tentar encontrar o servidor no banco de dados
                    try:
                        servidor = Servidor.objects.get(matricula=matricula)
                    except Servidor.DoesNotExist:
                        messages.error(request, f"Erro: Servidor com matrícula {matricula} não encontrado.")
                        continue

                    # Processar a data
                    try:
                        data_completa = parser.parse(str(data)).date()
                    except ValueError:
                        messages.error(request, f"Erro: Data inválida {data}.")
                        continue

                    # Verificar se a data já existe para o servidor
                    if Ajuda_Custo.objects.filter(matricula=servidor.matricula, data=data_completa).exists():
                        messages.warning(request, f'Registro já existente para o servidor {nome} na data {data}.')
                        continue

                    # Verificar total de horas do mês
                    inicio_do_mes = data_completa.replace(day=1)
                    fim_do_mes = (inicio_do_mes + timedelta(days=31)).replace(day=1) - timedelta(days=1)

                    registros_mes = Ajuda_Custo.objects.filter(
                        matricula=servidor.matricula,
                        data__range=[inicio_do_mes, fim_do_mes]
                    )

                    # Calcular o total de horas do mês
                    total_horas_mes = sum(
                        12 if registro.carga_horaria == '12 horas' else 24
                        for registro in registros_mes
                    )

                    horas_a_adicionar = 12 if carga_horaria == '12 horas' else 24

                    if total_horas_mes + horas_a_adicionar > 192:
                        messages.error(request, f'Limite de 192 horas mensais excedido para {nome} na data {data}.')
                        continue

                    # Verificação das datas majoradas
                    majorado = DataMajorada.objects.filter(data=data_completa).exists()

                    # Criar o registro de ajuda de custo
                    ajuda_custo = Ajuda_Custo(
                        matricula=servidor.matricula,
                        nome=servidor.nome,
                        data=data_completa,
                        unidade=unidade,
                        carga_horaria=carga_horaria,
                        majorado=majorado  # Adiciona a informação sobre se a data é majorada
                    )
                    ajuda_custo.save()
                    registros_inseridos = True

                if registros_inseridos:
                    messages.success(request, "Registros inseridos com sucesso!")
                else:
                    messages.info(request, "Nenhum registro foi inserido.")
            except Exception as e:
                messages.error(request, f"Erro ao processar o arquivo: {str(e)}")
                return redirect('ajuda_custo:upload_excel_rx2')
    else:
        form = UploadExcelRx2Form()

    return render(request, 'upload_excel_rx2.html', {'form': form})



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

    # Converte as datas em objetos datetime, se fornecidas
    data_inicial = parse_date(data_inicial) if data_inicial else None
    data_final = parse_date(data_final) if data_final else None

    # Filtrar os dados com base nos parâmetros
    queryset = Ajuda_Custo.objects.all()
    if query:
        queryset = queryset.filter(Q(nome__icontains=query) | Q(matricula__icontains=query))

    if data_inicial and data_final:
        queryset = queryset.filter(data__range=[data_inicial, data_final])
    elif data_inicial:
        queryset = queryset.filter(data__gte=data_inicial)
    elif data_final:
        queryset = queryset.filter(data__lte=data_final)

    # Adicionando um print para verificar o queryset
    print(f"Queryset após filtros: {queryset}")

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

    ws.column_dimensions['I'].width = 40  # Largura da coluna I (Datas 12 Horas)
    ws.column_dimensions['J'].width = 40  # Largura da coluna J (Datas 24 Horas)

    # Função para formatar as datas em múltiplas linhas
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

        # Define a largura da coluna, garantindo que as colunas I e J mantenham a largura definida
        if column_letter in ['I', 'J']:
            ws.column_dimensions[column_letter].width = 50  # Garante que as colunas I e J tenham largura fixa
        else:
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

    print(query, data_final, data_inicial)
    # Converte as datas em objetos datetime, se fornecidas
    data_inicial = parse_date(data_inicial) if data_inicial else None
    data_final = parse_date(data_final) if data_final else None

    # Filtrar os dados com base nos parâmetros
    queryset = Ajuda_Custo.objects.all()
    if query:
        queryset = queryset.filter(Q(nome__icontains=query) | Q(matricula__icontains=query))

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
        data = item.data.strftime('%d/%m/%Y')

        if item.carga_horaria == '12 horas':
            carga_horaria = '12 horas'
        else:
            carga_horaria = '24 horas'

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
    paginate_by = 20  # Quantidade de registros por página

    def get_queryset(self):
        # Captura os parâmetros de pesquisa
        user = self.request.user
        query = self.request.GET.get('query', '')
        data_inicial = self.request.GET.get('dataInicial')
        data_final = self.request.GET.get('dataFinal')

        # Converte as datas em objetos datetime, se fornecidas
        data_inicial = parse_date(data_inicial) if data_inicial else None
        data_final = parse_date(data_final) if data_final else None

        # Cria o filtro básico com base na query de pesquisa
        if user.groups.filter(name__in=['Administrador', 'GerGesipe']).exists():
            queryset = Ajuda_Custo.objects.all()
        else:
            queryset = Ajuda_Custo.objects.filter(matricula=user.matricula)

        if query:
            queryset = queryset.filter(
                Q(nome__icontains=query) | Q(matricula__icontains=query)
            )

        # Aplica os filtros de data se fornecidos
        if data_inicial and data_final:
            queryset = queryset.filter(data__range=[data_inicial, data_final])
        elif data_inicial:
            queryset = queryset.filter(data__gte=data_inicial)
        elif data_final:
            queryset = queryset.filter(data__lte=data_final)

        return queryset.order_by('nome')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('query', '')
        context['dataInicial'] = self.request.GET.get('dataInicial', '')
        context['dataFinal'] = self.request.GET.get('dataFinal', '')

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

        if form.is_valid():
            mes = request.POST.get('mes')
            ano = request.POST.get('ano')
            dias = request.POST.getlist('dia')
            unidades = request.POST.getlist('unidade')
            cargas_horarias = request.POST.getlist('carga_horaria')

            try:
                # Obter o servidor com base no usuário logado
                try:
                    servidor = Servidor.objects.get(matricula=self.request.user.matricula)
                except Servidor.DoesNotExist:
                    messages.error(self.request, 'Erro: Servidor não encontrado.')
                    return redirect(self.success_url)

                mes_int = int(mes)
                ano_int = int(ano)

                # Calcular o total de horas já marcadas para o mês
                inicio_do_mes = datetime(ano_int, mes_int, 1)
                fim_do_mes = (inicio_do_mes + timedelta(days=31)).replace(day=1) - timedelta(days=1)

                registros_mes = Ajuda_Custo.objects.filter(
                    matricula=servidor.matricula,
                    data__range=[inicio_do_mes, fim_do_mes]
                )

                # Inicializa a variável para armazenar a soma das cargas horárias passadas
                carga_horaria_passado_total = 0

                # Iterar sobre os registros do mês e somar as cargas horárias
                for registro in registros_mes:
                    carga_horaria_passado = registro.carga_horaria.strip()  # Acessa o campo 'carga_horaria'

                    # Verifica e converte o valor de 'carga_horaria'
                    if carga_horaria_passado == "12 horas":
                        carga_horaria_passado_total += 12
                    elif carga_horaria_passado == "24 horas":
                        carga_horaria_passado_total += 24

                # Agora 'carga_horaria_passado_total' contém a soma das horas já registradas no mês
                total_horas_mes = carga_horaria_passado_total or 0

                # Obter limite de horas do servidor
                try:
                    limite = LimiteAjudaCusto.objects.get(servidor=servidor)
                    limite_horas = limite.limite_horas
                except LimiteAjudaCusto.DoesNotExist:
                    messages.error(self.request, 'Limite de horas não definido. Contate o administrador.')
                    return redirect(self.success_url)

                # Calcula a soma das horas que o servidor pretende adicionar
                horas_a_adicionar_total = 0
                for carga_horaria in cargas_horarias:
                    carga_horaria_limpa = carga_horaria.strip().replace(' horas', '')  # Remove ' horas'
                    horas_a_adicionar_total += int(carga_horaria_limpa)  # Somar as horas

                # Verificar se o total de horas no mês excederá o limite global de 192 horas
                if total_horas_mes + horas_a_adicionar_total > 192:  # Limite global
                    messages.error(self.request,
                                   f'Limite global de 192 horas mensais excedido. Total pretendido: {total_horas_mes + horas_a_adicionar_total}.')
                    return self.form_invalid(form)

                # Verificar se o total de horas no mês excederá o limite individual do servidor
                if total_horas_mes + horas_a_adicionar_total > limite_horas:
                    messages.error(self.request,
                                   f'O limite individual de {limite_horas} horas foi excedido. Total pretendido: {total_horas_mes + horas_a_adicionar_total}.')
                    return self.form_invalid(form)

                # Processar as novas datas, unidades e cargas horárias, já que os limites foram verificados
                for dia, unidade, carga_horaria in zip(dias, unidades, cargas_horarias):
                    try:
                        data_completa = datetime.strptime(f"{dia}/{mes}/{ano}", "%d/%m/%Y").date()

                        # Limpar e converter a carga horária
                        carga_horaria_limpa = carga_horaria.strip().replace(' horas', '')
                        horas_a_adicionar = int(carga_horaria_limpa)

                        # Verificar se o servidor já marcou essa data
                        if Ajuda_Custo.objects.filter(matricula=servidor.matricula, data=data_completa).exists():
                            messages.error(self.request, f'O servidor já possui uma entrada para {dia}/{mes}/{ano}.')
                            return self.form_invalid(form)

                        # Atualiza o total de horas mensais após a verificação
                        total_horas_mes += horas_a_adicionar

                        # Garantimos que a carga horária seja "12 horas" ou "24 horas" como string
                        carga_horaria_final = f"{horas_a_adicionar} horas"

                        # Cria o objeto Ajuda_Custo e salva no banco de dados
                        ajuda_custo = Ajuda_Custo(
                            matricula=self.request.user.matricula,
                            nome=self.request.user.nome_completo,
                            data=data_completa,
                            unidade=unidade,
                            carga_horaria=carga_horaria_final,
                            majorado=DataMajorada.objects.filter(data=data_completa).exists()
                        )
                        ajuda_custo.save()

                    except ValueError:
                        messages.error(self.request, f'Erro: Data inválida - {dia}/{mes}/{ano}')
                        return self.form_invalid(form)

                # Após inserir novos registros, verificar se um novo arquivo de folha assinada foi enviado
                novo_arquivo = form.cleaned_data.get('folha_assinada')
                if novo_arquivo:
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

                messages.success(self.request, 'Datas adicionadas e atualizadas com sucesso!')
                return redirect(self.success_url)

            except Exception as e:
                print(f'Erro: {e}')
                messages.error(self.request, 'Ocorreu um erro interno. Tente novamente mais tarde.')
                return self.form_invalid(form)

        else:
            messages.error(self.request, 'Erro no Cadastro, Confira os Dados e Tente Novamente.')
            return self.form_invalid(form)


class AdminCadastrar(LoginRequiredMixin, UserPassesTestMixin, FormView):
    model = Ajuda_Custo
    form_class = AdminDatasForm
    template_name = 'admin_cadastrar.html'
    success_url = reverse_lazy('ajuda_custo:admin_cadastrar')

    def test_func(self):
        user = self.request.user
        grupos_permitidos = ['Administrador', 'GerGesipe']
        return user.groups.filter(name__in=grupos_permitidos).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return render(self.request, '403.html', status=403)

    def form_valid(self, form):
        try:
            mes = form.cleaned_data['mes']
            ano = form.cleaned_data['ano']
            unidade = form.cleaned_data['unidade']
            dias_12h = form.cleaned_data['dias_12h']
            dias_24h = form.cleaned_data['dias_24h']

            dias_12h_list = [dia.strip() for dia in dias_12h.split(',') if dia.strip()]
            dias_24h_list = [dia.strip() for dia in dias_24h.split(',') if dia.strip()]

            matricula = self.request.POST.get('matricula')
            servidor = Servidor.objects.get(matricula=matricula)

            mes_int = int(mes)
            ano_int = int(ano)

            for dia in dias_12h_list + dias_24h_list:
                try:
                    data_completa = datetime.strptime(f"{dia}/{mes}/{ano}", "%d/%m/%Y").date()

                    if Ajuda_Custo.objects.filter(matricula=servidor.matricula, data=data_completa).exists():
                        messages.error(self.request, f'O servidor já possui uma entrada para {dia}/{mes}/{ano}.')
                        return redirect(self.success_url)

                    inicio_do_mes = data_completa.replace(day=1)
                    fim_do_mes = (inicio_do_mes + timedelta(days=31)).replace(day=1) - timedelta(days=1)

                    registros_mes = Ajuda_Custo.objects.filter(
                        matricula=servidor.matricula,
                        data__range=[inicio_do_mes, fim_do_mes]
                    )

                    total_horas_mes = sum(12 if reg.carga_horaria == '12 horas' else 24 for reg in registros_mes)
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

        except Servidor.DoesNotExist:
            messages.error(self.request, 'Erro: Servidor não encontrado.')
            return redirect(self.success_url)

        except Exception as e:
            logging.error(f"Erro ao adicionar Ajuda_Custo: {str(e)}")
            messages.error(self.request, f'Erro: {str(e)}')
            return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, 'Erro no Cadastro, Confira os Dados e Tente Novamente.')
        return super().form_invalid(form)
class HorasLimite(LoginRequiredMixin, UserPassesTestMixin, FormView ):
    model = LimiteAjudaCusto
    form_class = LimiteAjudaCustoForm
    template_name = 'horas_limite.html'
    success_url = reverse_lazy('ajuda_custo:horas_limite')

    # Verifica se o usuário pertence a determinados grupos
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
        servidor = form.cleaned_data['servidor']
        limite_horas = form.cleaned_data['limite_horas']

        # Verifica se o servidor já possui um limite definido
        limite_existente, created = LimiteAjudaCusto.objects.update_or_create(
            servidor=servidor,
            defaults={'limite_horas': limite_horas}
        )

        if created:
            messages.success(self.request, 'Limite de horas adicionado com sucesso!')
        else:
            messages.success(self.request, 'Limite de horas atualizado com sucesso!')

        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtenha o valor da consulta de pesquisa, se houver
        query = self.request.GET.get('query', '')

        # Filtra por nome ou matrícula, se houver uma consulta
        if query:
            cargas = LimiteAjudaCusto.objects.filter(
                Q(servidor__nome__icontains=query) | Q(servidor__matricula__icontains=query)
            ).order_by('servidor__nome')  # Ordena os servidores por nome
        else:
            cargas = LimiteAjudaCusto.objects.all().order_by('servidor__nome')  # Ordena os servidores por nome

        # Adiciona a paginação

        paginator = Paginator(cargas, 20)  # Mostra 20 registros por página

        paginator = Paginator(cargas, 20)  # Mostra 10 registros por página

        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Adiciona os dados ao contexto
        context['carga_horaria'] = page_obj
        context['page_obj'] = page_obj
        context['query'] = query
        return context

def excluir_limite(request, pk):
    limite = get_object_or_404(LimiteAjudaCusto, pk=pk)
    limite.delete()
    messages.success(request, 'Limite de horas excluído com sucesso!')
    return redirect('ajuda_custo:horas_limite')
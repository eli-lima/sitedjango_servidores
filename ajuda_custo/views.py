from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, CreateView, FormView, ListView, View
from .models import Ajuda_Custo, DataMajorada, LimiteAjudaCusto
from .forms import AjudaCustoForm, AdminDatasForm, LimiteAjudaCustoForm
from django.urls import reverse_lazy
from datetime import datetime
from django.contrib import messages
from django.db.models import Q
from openpyxl.styles import Alignment
from django.utils.dateparse import parse_date
from django.http import HttpResponse
from openpyxl import Workbook
import pandas as pd
from django.http import JsonResponse
from servidor.models import Servidor
from datetime import timedelta
from django.core.paginator import Paginator



# Create your views here.


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

        if carga_horaria == '12_horas':
            dados_matriculas[matricula]['Datas 12 Horas'].append(pd.to_datetime(data))
            dados_matriculas[matricula]['Carga Horária Total'] += 12
            if majorado:
                dados_matriculas[matricula]['Horas Majoradas'] += 12
                dados_matriculas[matricula]['12h'] += 1
            else:
                dados_matriculas[matricula]['Horas Normais'] += 12
                dados_matriculas[matricula]['12h'] += 1

        elif carga_horaria == '24_horas':
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
    response['Content-Disposition'] = 'attachment; filename=relatorio_ajuda_custo.xlsx'

    # Criar uma nova planilha Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Relatório Ajuda Custo"

    # Adicionar o período de datas no topo da planilha
    ws.merge_cells('A1:J1')
    ws['A1'] = f"Período: {data_inicial.strftime('%d/%m/%Y')} a {data_final.strftime('%d/%m/%Y')}" if data_inicial and data_final else 'Período: Todos os Dados'

    # Adicionar os cabeçalhos das colunas
    cabecalhos = ['Matrícula', 'Nome', 'Carga Horária Total', 'Horas Majoradas', 'Horas Normais', 'Total',
                  '12h', '24h', 'Datas 12 Horas', 'Datas 24 Horas']
    ws.append(cabecalhos)

    # Função para formatar as datas em múltiplas linhas
    def formatar_datas_em_linhas(datas):
        linhas = []
        for i in range(0, len(datas), 3):  # Agrupa a cada 3 datas
            linhas.append(', '.join(datas[i:i+3]))
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

        if item.carga_horaria == '12_horas':
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
    response['Content-Disposition'] = 'attachment; filename=relatorio_ajuda_custo.xlsx'
    wb.save(response)

    return response


class AjudaCusto(LoginRequiredMixin, ListView):
    model = Ajuda_Custo
    template_name = "ajuda_custo.html"
    context_object_name = 'datas'
    paginate_by = 10  # Quantidade de registros por página

    def get_queryset(self):
        # Captura os parâmetros de pesquisa
        query = self.request.GET.get('query', '')
        data_inicial = self.request.GET.get('dataInicial')
        data_final = self.request.GET.get('dataFinal')

        # Converte as datas em objetos datetime, se fornecidas
        data_inicial = parse_date(data_inicial) if data_inicial else None
        data_final = parse_date(data_final) if data_final else None

        # Cria o filtro básico com base na query de pesquisa
        queryset = Ajuda_Custo.objects.all()

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

        # Ordena por nome
        return queryset.order_by('nome')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('query', '')
        context['dataInicial'] = self.request.GET.get('dataInicial', '')
        context['dataFinal'] = self.request.GET.get('dataFinal', '')
        return context


class RelatorioAjudaCusto(LoginRequiredMixin, ListView):
    model = Ajuda_Custo
    template_name = "relatorio_ajuda_custo.html"
    context_object_name = 'datas'
    paginate_by = 50  # Quantidade de registros por página

    def get_queryset(self):
        # Captura os parâmetros de pesquisa
        query = self.request.GET.get('query', '')
        data_inicial = self.request.GET.get('dataInicial')
        data_final = self.request.GET.get('dataFinal')

        # Converte as datas em objetos datetime, se fornecidas
        data_inicial = parse_date(data_inicial) if data_inicial else None
        data_final = parse_date(data_final) if data_final else None

        # Cria o filtro básico com base na query de pesquisa
        queryset = Ajuda_Custo.objects.all()

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

        # Ordena por nome
        return queryset.order_by('nome')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('query', '')
        context['dataInicial'] = self.request.GET.get('dataInicial', '')
        context['dataFinal'] = self.request.GET.get('dataFinal', '')
        return context

    def get(self, request, *args, **kwargs):
        action = request.GET.get('action')
        if action == 'export_excel':
            return exportar_excel(request)
        elif action == 'excel_detalhado':
            return excel_detalhado(request)
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

            # Obter o servidor com base no usuário logado
            try:
                servidor = Servidor.objects.get(matricula=self.request.user.matricula)
            except Servidor.DoesNotExist:
                messages.error(self.request, 'Erro: Servidor não encontrado.')
                return redirect(self.success_url)

            # Busca o limite de horas mensal para o servidor
            try:
                limite = LimiteAjudaCusto.objects.get(servidor=servidor)
                limite_horas = limite.limite_horas
            except LimiteAjudaCusto.DoesNotExist:
                messages.error(self.request, 'Limite de horas não definido. Contate o administrador.')
                return redirect(self.success_url)

            mes_int = int(mes)
            ano_int = int(ano)

            for dia, unidade, carga_horaria in zip(dias, unidades, cargas_horarias):
                try:
                    data_completa = datetime.strptime(f"{dia}/{mes}/{ano}", "%d/%m/%Y").date()

                    # Definindo o início e o fim do mês para a consulta
                    inicio_do_mes = data_completa.replace(day=1)
                    fim_do_mes = (inicio_do_mes + timedelta(days=31)).replace(day=1) - timedelta(days=1)

                    # Calcula o total de horas já registradas para o mês
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

                    # Converte a carga horária atual para horas
                    horas_a_adicionar = 12 if carga_horaria == '12 horas' else 24

                    # Verifica se o total de horas no mês ultrapassa o limite permitido
                    if total_horas_mes + horas_a_adicionar > limite_horas:
                        messages.error(self.request, f'Limite de {limite_horas} horas/mês excedido para {dia}/{mes}/{ano}.')
                        return self.form_invalid(form)

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

                except ValueError:
                    messages.error(self.request, f'Erro: Data inválida - {dia}/{mes}/{ano}')
                    return self.form_invalid(form)

            messages.success(self.request, 'Datas adicionadas com sucesso!')
            return redirect(self.success_url)
        else:
            messages.error(self.request, 'Erro no Cadastro, Confira os Dados e Tente Novamente.')
            return self.form_invalid(form)


class AdminCadastrar(LoginRequiredMixin, FormView):
    model = Ajuda_Custo
    form_class = AdminDatasForm
    template_name = 'admin_cadastrar.html'
    success_url = reverse_lazy('ajuda_custo:admin_cadastrar')

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


class HorasLimite(LoginRequiredMixin, FormView):
    model = LimiteAjudaCusto
    form_class = LimiteAjudaCustoForm
    template_name = 'horas_limite.html'
    success_url = reverse_lazy('ajuda_custo:horas_limite')

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
            )
        else:
            cargas = LimiteAjudaCusto.objects.all()

        # Adiciona a paginação
        paginator = Paginator(cargas, 10)  # Mostra 10 registros por página
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
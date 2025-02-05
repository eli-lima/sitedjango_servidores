from .models import Ajuda_Custo, DataMajorada
from servidor.models import Servidor
from datetime import timedelta
from django.db import IntegrityError
from dateutil import parser
import re
import pandas as pd
from celery import shared_task
import requests
from collections import defaultdict
from django.contrib import messages


@shared_task
def process_batch(df_batch):
    registros_inseridos = False
    ajuda_custos_para_inserir = []
    horas_por_servidor = defaultdict(int)  # Dicionário para armazenar as horas acumuladas por servidor e mês
    datas_processadas = set()
    erros = []  # Lista para armazenar as informações sobre falhas

    # Pré-processamento: Agrupa as matrículas e datas para consulta única no banco
    matriculas_datas = [(re.sub(r'\D', '', str(row['Matrícula'])).lstrip('0'), parser.parse(str(row['Data'])).date())
                        for row in df_batch if row['Matrícula']]

    print(f'matriculas banco de dados: {matriculas_datas}')

    # Consulta única para verificar registros existentes no banco
    registros_existentes = Ajuda_Custo.objects.filter(
        matricula__in=[md[0] for md in matriculas_datas],
        data__in=[md[1] for md in matriculas_datas]
    ).values('matricula', 'data', 'carga_horaria')

    # Cria um conjunto de tuplas (matrícula, data) para verificação rápida de duplicidade
    registros_existentes_set = {(r['matricula'], r['data']) for r in registros_existentes}

    # Pré-calcula as horas acumuladas por servidor e mês
    for registro in registros_existentes:
        matricula = registro['matricula']
        data = registro['data']
        mes_ano = (data.year, data.month)
        carga_horaria_passado = registro['carga_horaria'].strip()

        if carga_horaria_passado == "12 horas":
            horas_por_servidor[(matricula, mes_ano)] += 12
        elif carga_horaria_passado == "24 horas":
            horas_por_servidor[(matricula, mes_ano)] += 24

    for row in df_batch:  # Agora df_batch é uma lista de dicionários
        matricula_raw = row['Matrícula']
        if not matricula_raw:
            erros.append("Erro: Matrícula vazia encontrada.")
            continue

        matricula = re.sub(r'\D', '', str(matricula_raw)).lstrip('0')
        unidade = row['Unidade']
        nome = row['Nome']
        data = row['Data']
        carga_horaria_raw = row['Carga Horaria']

        # Converte a carga horária de texto para número inteiro
        carga_horaria = 0
        if carga_horaria_raw.strip() == "12 horas":
            carga_horaria = 12
        elif carga_horaria_raw.strip() == "24 horas":
            carga_horaria = 24
        else:
            erros.append(f"Erro: Carga horária inválida '{carga_horaria_raw}' para o servidor {nome}.")
            continue

        try:
            servidor = Servidor.objects.get(matricula=matricula)
        except Servidor.DoesNotExist:
            erros.append(f"Erro: Servidor com matrícula {matricula} não encontrado.")
            continue

        try:
            data_completa = parser.parse(str(data)).date()
        except ValueError:
            erros.append(f"Erro: Data inválida {data} para o servidor {nome}.")
            continue

        # Verificar se a data já foi processada neste lote
        if (servidor.matricula, data_completa) in datas_processadas:
            erros.append(f"Registro duplicado para o servidor {nome} na data {data_completa}.")
            continue

        # Verificar no banco de dados se já existe um registro para a mesma matrícula e data
        if (servidor.matricula, data_completa) in registros_existentes_set:
            erros.append(f"Erro: Registro já existe para o servidor {nome} na data {data_completa}.")
            continue

        datas_processadas.add((servidor.matricula, data_completa))

        # Extraindo mês e ano da data
        mes_ano = (data_completa.year, data_completa.month)

        # Verificar se a soma da carga horária do mês excede 192 horas
        horas_mes_atual = horas_por_servidor[(servidor.matricula, mes_ano)] + carga_horaria
        print(f'horas do mes atual: {horas_mes_atual}')

        if horas_mes_atual > 192:
            erros.append(
                f"Limite mensal de 192 horas excedido para o servidor {nome} no mês {data_completa.strftime('%m/%Y')}.")
            continue

        # Atualiza o dicionário com as horas acumuladas
        horas_por_servidor[(servidor.matricula, mes_ano)] = horas_mes_atual
        print(f'dicionarios horas por servidor: {horas_por_servidor}')

        majorado = DataMajorada.objects.filter(data=data_completa).exists()

        ajuda_custos_para_inserir.append(Ajuda_Custo(
            matricula=servidor.matricula,
            nome=servidor.nome,
            data=data_completa,
            unidade=unidade,
            carga_horaria=carga_horaria_raw,  # Armazena como texto original
            majorado=majorado
        ))

    # Inserir dados em massa
    try:
        if ajuda_custos_para_inserir:
            Ajuda_Custo.objects.bulk_create(ajuda_custos_para_inserir)
            registros_inseridos = True
    except IntegrityError as e:
        erros.append(f"Erro de integridade durante a inserção: {str(e)}")

    if registros_inseridos:
        print("Registros inseridos com sucesso!")
    else:
        print("Nenhum registro foi inserido.")

    if erros:
        print("Erros encontrados:")
        for erro in erros:
            print(erro)

    return erros  # Retorna a lista de erros para feedback



@shared_task(bind=True)
def process_excel_file(self, cloudinary_url):
    try:
        # Fazer o download do arquivo do Cloudinary
        response = requests.get(cloudinary_url)
        response.raise_for_status()

        # Ler o arquivo Excel
        df = pd.read_excel(response.content)

        # Lógica de processamento dos dados
        batch_size = 10000  # Tamanho do lote (ajuste conforme necessário)
        total_registros = df.shape[0]
        print(f"Total de registros a processar: {total_registros}")
        erros_totais = []

        # Processa o arquivo em lotes
        for start in range(0, total_registros, batch_size):
            end = min(start + batch_size, total_registros)
            df_batch = df.iloc[start:end]

            # Converte o batch para uma lista de dicionários
            df_batch_dict = df_batch.to_dict(orient='records')
            print(f"Processando lote de registros: {start} a {end}")

            # Chama a função process_batch para processar o lote
            result = process_batch(df_batch_dict)  # Chama a função que já processa os dados
            erros_totais.extend(result)

        print(f"Processamento concluído. Erros totais: {len(erros_totais)}")

        # Retorna status e erros, se houver
        return {'status': 'sucesso' if not erros_totais else 'erro', 'erros': erros_totais}

    except Exception as e:
        print(f"Ocorreu um erro durante o processamento: {str(e)}")  # Print do erro
        return {'status': 'falha', 'mensagem': str(e)}
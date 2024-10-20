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


@shared_task
def process_batch(df_batch):
    ajuda_custos_para_inserir = []
    erros = []  # Lista para armazenar as informações sobre falhas
    datas_processadas = defaultdict(set)  # Para rastrear datas processadas por servidor

    # Primeiro, percorremos o DataFrame para calcular as horas a serem adicionadas
    horas_a_adicionar_por_servidor = defaultdict(int)  # Para rastrear horas a serem adicionadas
    dados_a_inserir = []

    for row in df_batch:  # Agora df_batch é uma lista de dicionários
        matricula_raw = row['Matrícula']
        matricula = re.sub(r'\D', '', str(matricula_raw)).lstrip('0')
        unidade = row['Unidade']
        nome = row['Nome']
        data = row['Data']
        carga_horaria_raw = row['Carga Horaria']

        # Tentar buscar o servidor
        try:
            servidor = Servidor.objects.get(matricula=matricula)
        except Servidor.DoesNotExist:
            erros.append(f"Servidor com matrícula {matricula} não encontrado.")
            continue  # Pular se não encontrar o servidor

        # Processar data
        try:
            data_completa = parser.parse(str(data)).date()  # Certifique-se de que isso retorna um objeto date
        except ValueError:
            erros.append(f"Data inválida para a matrícula {matricula}: {data}")
            continue  # Pular se a data for inválida

        # Verificar se a data já foi processada para este servidor
        if data_completa in datas_processadas[servidor.matricula]:
            erros.append(f"Registro duplicado na planilha para a matrícula {matricula} na data {data_completa}.")
            continue

        datas_processadas[servidor.matricula].add(data_completa)

        # Calcular a carga horária a ser adicionada
        horas_a_adicionar = 12 if carga_horaria_raw == '12 horas' else 24
        horas_a_adicionar_por_servidor[servidor.matricula] += horas_a_adicionar

        # Adicionar dados para inserção
        dados_a_inserir.append((servidor.matricula, nome, data_completa, unidade, carga_horaria_raw))

    # Após coletar todos os dados, verifique as horas no banco
    for matricula, nome, data_completa, unidade, carga_horaria_raw in dados_a_inserir:
        # Calcular total de horas do mês
        inicio_do_mes = data_completa.replace(day=1)
        fim_do_mes = (inicio_do_mes + timedelta(days=31)).replace(day=1) - timedelta(days=1)

        registros_mes = Ajuda_Custo.objects.filter(
            matricula=matricula,
            data__range=[inicio_do_mes, fim_do_mes]
        )

        # Calcular o total de horas do mês
        total_horas_mes = sum(
            12 if registro.carga_horaria == '12 horas' else 24
            for registro in registros_mes
        )

        # Calcular as horas que seriam adicionadas
        horas_a_adicionar = horas_a_adicionar_por_servidor[matricula]

        # Verificar se o limite de 192 horas é excedido
        if total_horas_mes + horas_a_adicionar > 192:
            erros.append(f'Limite de 192 horas mensais excedido para {nome} na data {data_completa}.')
            continue

        # Verificar se o registro já existe
        if not Ajuda_Custo.objects.filter(matricula=matricula, data=data_completa).exists():
            majorado = DataMajorada.objects.filter(data=data_completa).exists()
            ajuda_custos_para_inserir.append(Ajuda_Custo(
                matricula=matricula,
                nome=nome,
                data=data_completa,
                unidade=unidade,
                carga_horaria=carga_horaria_raw,  # Armazena a carga horária original
                majorado=majorado
            ))
        else:
            erros.append(f"Registro já existente para a matrícula {matricula} e data {data_completa}.")

    # Inserir dados em massa
    try:
        if ajuda_custos_para_inserir:
            Ajuda_Custo.objects.bulk_create(ajuda_custos_para_inserir)
    except IntegrityError as e:
        erros.append(f"Erro de integridade durante a inserção: {str(e)}")

    return erros  # Retorna a lista de erros para feedback


@shared_task(bind=True)
def process_excel_file(self, cloudinary_url):
    print(f"Iniciando o processamento do arquivo com URL: {cloudinary_url}")  # Print de início
    try:
        # Fazer o download do arquivo do Cloudinary
        response = requests.get(cloudinary_url)
        response.raise_for_status()
        print("Arquivo baixado com sucesso.")  # Print de sucesso no download

        # Ler o arquivo Excel
        df = pd.read_excel(response.content)
        print(f"Arquivo Excel lido. Total de registros: {df.shape[0]}")  # Print do total de registros

        # Lógica de processamento dos dados
        batch_size = 2000
        total_registros = df.shape[0]
        print(f"Total de registros a processar: {total_registros}")
        erros_totais = []

        for start in range(0, total_registros, batch_size):
            end = min(start + batch_size, total_registros)
            df_batch = df.iloc[start:end]

            # Converte o batch para uma lista de dicionários
            df_batch_dict = df_batch.to_dict(orient='records')
            print(f"Processando lote de registros: {start} a {end}")

            # Processa o lote e acumula erros
            result = process_batch(df_batch_dict)  # Chama a função que já processa os dados
            erros_totais.extend(result)

        print(f"Processamento concluído. Erros totais: {len(erros_totais)}")

        # Retorna status e erros, se houver
        return {'status': 'sucesso' if not erros_totais else 'erro', 'erros': erros_totais}

    except Exception as e:
        print(f"Ocorreu um erro durante o processamento: {str(e)}")  # Print do erro
        return {'status': 'falha', 'mensagem': str(e)}

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
    registros_inseridos = False
    ajuda_custos_para_inserir = []
    datas_processadas = set()
    erros = []  # Lista para armazenar as informações sobre falhas

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

        # **Verificar no banco de dados se já existe um registro para a mesma matrícula e data**
        registro_existente = Ajuda_Custo.objects.filter(matricula=servidor.matricula, data=data_completa).exists()
        if registro_existente:
            erros.append(f"Erro: Registro já existe para o servidor {nome} na data {data_completa}.")
            continue

        datas_processadas.add((servidor.matricula, data_completa))

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
        batch_size = 10000
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

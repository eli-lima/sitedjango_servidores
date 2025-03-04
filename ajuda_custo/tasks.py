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
from datetime import datetime


@shared_task
def process_batch(df_batch):
    registros_inseridos = False
    ajuda_custos_para_inserir = []
    horas_por_servidor = defaultdict(int)
    datas_processadas = set()
    erros = []

    # Pré-calcular as horas já registradas no banco de dados
    servidores_no_lote = set(row['Matrícula'] for row in df_batch if row['Matrícula'])
    meses_no_lote = set((parser.parse(str(row['Data'])).date().strftime('%Y-%m') for row in df_batch if row['Data']))

    registros_banco = Ajuda_Custo.objects.filter(
        matricula__in=servidores_no_lote,
        data__year__in=[datetime.strptime(mes, '%Y-%m').year for mes in meses_no_lote],
        data__month__in=[datetime.strptime(mes, '%Y-%m').month for mes in meses_no_lote]
    )

    for registro in registros_banco:
        mes_ano = (registro.data.year, registro.data.month)
        carga_horaria_passado = registro.carga_horaria.strip()
        if carga_horaria_passado == "12 horas":
            horas_por_servidor[(registro.matricula, mes_ano)] += 12
        elif carga_horaria_passado == "24 horas":
            horas_por_servidor[(registro.matricula, mes_ano)] += 24

    for row in df_batch:
        matricula_raw = row['Matrícula']
        if not matricula_raw:
            erros.append("Erro: Matrícula vazia encontrada.")
            continue

        # Limpa a matrícula e converte para inteiro
        try:
            matricula = int(re.sub(r'\D', '', str(matricula_raw)).lstrip('0'))
        except ValueError:
            erros.append(f"Erro: Matrícula inválida '{matricula_raw}' para o servidor {row['Nome']}.")
            continue

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

        if (servidor.matricula, data_completa) in datas_processadas:
            erros.append(f"Registro duplicado para o servidor {nome} na data {data_completa}.")
            continue

        registro_existente = Ajuda_Custo.objects.filter(matricula=servidor.matricula, data=data_completa).exists()
        if registro_existente:
            erros.append(f"Erro: Registro já existe para o servidor {nome} na data {data_completa}.")
            continue

        datas_processadas.add((servidor.matricula, data_completa))

        mes_ano = (data_completa.year, data_completa.month)
        horas_mes_atual = horas_por_servidor.get((servidor.matricula, mes_ano), 0)

        if horas_mes_atual + carga_horaria > 192:
            erros.append(f"Limite mensal de 192 horas excedido para o servidor {nome} no mês {data_completa.strftime('%m/%Y')}.")
            continue

        horas_por_servidor[(servidor.matricula, mes_ano)] = horas_mes_atual + carga_horaria

        majorado = DataMajorada.objects.filter(data=data_completa).exists()

        ajuda_custos_para_inserir.append(Ajuda_Custo(
            matricula=servidor.matricula,
            nome=servidor.nome,
            data=data_completa,
            unidade=unidade,
            carga_horaria=carga_horaria_raw,
            majorado=majorado
        ))

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

    return erros


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

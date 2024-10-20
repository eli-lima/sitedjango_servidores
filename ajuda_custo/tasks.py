# tasks.py
from celery import shared_task
from .models import Ajuda_Custo, DataMajorada
from servidor.models import Servidor
from datetime import timedelta
from django.db import IntegrityError
from dateutil import parser
import re


@shared_task
def process_batch(df_batch):
    ajuda_custos_para_inserir = []
    erros = []  # Lista para armazenar as informações sobre falhas

    for _, row in df_batch.iterrows():
        matricula_raw = row['Matrícula']
        matricula = re.sub(r'\D', '', str(matricula_raw)).lstrip('0')
        unidade = row['Unidade']
        nome = row['Nome']
        data = row['Data']
        carga_horaria = row['Carga Horaria']

        # Tentar buscar o servidor
        try:
            servidor = Servidor.objects.get(matricula=matricula)
        except Servidor.DoesNotExist:
            erros.append(f"Servidor com matrícula {matricula} não encontrado.")
            continue  # Pular se não encontrar o servidor

        # Processar data
        try:
            data_completa = parser.parse(str(data)).date()
        except ValueError:
            erros.append(f"Data inválida para a matrícula {matricula}: {data}")
            continue  # Pular se a data for inválida

        # Verificar se o registro já existe
        if not Ajuda_Custo.objects.filter(matricula=servidor.matricula, data=data_completa).exists():
            majorado = DataMajorada.objects.filter(data=data_completa).exists()
            ajuda_custos_para_inserir.append(Ajuda_Custo(
                matricula=servidor.matricula,
                nome=servidor.nome,
                data=data_completa,
                unidade=unidade,
                carga_horaria=carga_horaria,
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

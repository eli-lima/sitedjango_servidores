from .models import Ajuda_Custo, DataMajorada
from servidor.models import Servidor
from datetime import timedelta
from django.db import IntegrityError
from dateutil import parser
import re
import pandas as pd
from celery import shared_task
import requests
import cloudinary


@shared_task
def process_batch(df_batch):
    ajuda_custos_para_inserir = []
    erros = []  # Lista para armazenar as informações sobre falhas

    for row in df_batch:  # Agora df_batch é uma lista de dicionários
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
            erros.append(f'Limite de 192 horas mensais excedido para {nome} na data {data}.')
            continue

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


@shared_task()
def process_excel_file(cloudinary_url, public_id):
    try:
        # Lógica de processamento do arquivo Excel (baixar, processar, etc.)
        print(f"Processando o arquivo: {cloudinary_url}")

        # Simulação de sucesso do processamento
        resultado = {"status": "sucesso"}

        print("Processamento concluído. Excluindo o arquivo do Cloudinary...")
        cloudinary.uploader.destroy(public_id, resource_type="raw")
        print(f"Arquivo com public_id {public_id} excluído do Cloudinary com sucesso.")

        return resultado

    except Exception as e:
        print(f"Erro durante o processamento: {str(e)}")

        # Tenta excluir o arquivo mesmo se houver erro no processamento
        try:
            cloudinary.uploader.destroy(public_id, resource_type="raw")
            print(f"Arquivo com public_id {public_id} excluído do Cloudinary após erro.")
        except Exception as delete_error:
            print(f"Erro ao excluir o arquivo após falha no processamento: {str(delete_error)}")

        return {"status": "falha", "erros": [str(e)]}

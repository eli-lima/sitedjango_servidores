from django.shortcuts import render, redirect
from django.contrib import messages

import pandas as pd
import requests
from collections import defaultdict
from .models import Interno
from celery import shared_task





@shared_task
def process_batch_internos(df_batch):
    registros_inseridos = False
    internos_para_inserir = []
    erros = []

    for row in df_batch:
        nome = row.get('Nome', '').strip()
        cpf = row.get('CPF', '').strip()
        data_nascimento = row.get('Data de Nascimento', '').strip()
        unidade = row.get('Unidade', '').strip()

        if not nome or not cpf:
            erros.append(f"Erro: Nome ou CPF inválido.")
            continue

        if Interno.objects.filter(cpf=cpf).exists():
            erros.append(f"Erro: Interno com CPF {cpf} já existe.")
            continue

        internos_para_inserir.append(Interno(nome=nome, cpf=cpf, data_nascimento=data_nascimento, unidade=unidade))

    try:
        if internos_para_inserir:
            Interno.objects.bulk_create(internos_para_inserir)
            registros_inseridos = True
    except Exception as e:
        erros.append(f"Erro ao inserir registros: {str(e)}")

    return erros


@shared_task(bind=True)
def process_excel_internos(self, cloudinary_url):
    try:
        response = requests.get(cloudinary_url)
        response.raise_for_status()
        df = pd.read_excel(response.content)
        batch_size = 5000
        erros_totais = []

        for start in range(0, len(df), batch_size):
            df_batch = df.iloc[start:start + batch_size].to_dict(orient='records')
            erros_totais.extend(process_batch_internos(df_batch))

        return {'status': 'sucesso' if not erros_totais else 'erro', 'erros': erros_totais}
    except Exception as e:
        return {'status': 'falha', 'mensagem': str(e)}
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

    print(f"📌 Processando lote de {len(df_batch)} registros...")  # Print para depuração

    for row in df_batch:
        nome = row.get('Nome', '').strip()
        cpf = row.get('CPF', '').strip()
        data_nascimento = row.get('Data de Nascimento', '').strip()
        unidade = row.get('Unidade', '').strip()

        print(f"🔍 Nome: {nome}, CPF: {cpf}, Data: {data_nascimento}, Unidade: {unidade}")  # Dados da linha

        if not nome or not cpf:
            erro_msg = f"❌ Erro: Nome ou CPF inválido. Linha: {row}"
            erros.append(erro_msg)
            print(erro_msg)
            continue

        if Interno.objects.filter(cpf=cpf).exists():
            erro_msg = f"⚠️ Erro: Interno com CPF {cpf} já existe."
            erros.append(erro_msg)
            print(erro_msg)
            continue

        internos_para_inserir.append(Interno(nome=nome, cpf=cpf, data_nascimento=data_nascimento, unidade=unidade))

    try:
        if internos_para_inserir:
            Interno.objects.bulk_create(internos_para_inserir)
            registros_inseridos = True
            print(f"✅ {len(internos_para_inserir)} registros inseridos com sucesso.")
    except Exception as e:
        erro_msg = f"🔥 Erro ao inserir registros: {str(e)}"
        erros.append(erro_msg)
        print(erro_msg)

    return erros


@shared_task(bind=True)
def process_excel_internos(self, cloudinary_url):
    try:
        print(f"📥 Baixando arquivo do Cloudinary: {cloudinary_url}")
        response = requests.get(cloudinary_url)
        response.raise_for_status()

        print("📊 Convertendo Excel para DataFrame...")
        df = pd.read_excel(response.content)

        print(f"📊 DataFrame carregado com {len(df)} registros.")

        batch_size = 5000
        erros_totais = []

        for start in range(0, len(df), batch_size):
            df_batch = df.iloc[start:start + batch_size].to_dict(orient='records')
            print(f"🚀 Enviando lote {start // batch_size + 1} para processamento...")
            erros_totais.extend(process_batch_internos(df_batch))

        print(f"✅ Processamento concluído. Total de erros: {len(erros_totais)}")

        return {'status': 'sucesso' if not erros_totais else 'erro', 'erros': erros_totais}
    except Exception as e:
        erro_msg = f"🔥 Erro geral no processamento: {str(e)}"
        print(erro_msg)
        return {'status': 'falha', 'mensagem': erro_msg}

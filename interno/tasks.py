from django.shortcuts import render, redirect
from django.contrib import messages

import pandas as pd
import requests
from collections import defaultdict
from .models import Interno
from celery import shared_task
from django.utils import timezone
from django.db import transaction





@shared_task
def process_batch_internos(df_batch):
    novos_registros = []
    atualizacoes = []
    erros = []

    print(f"📌 Processando lote de {len(df_batch)} registros...")

    for row in df_batch:
        prontuario = str(row.get('prontuario', '')).strip()
        nome = row.get('nome', '').strip()
        cpf = row.get('cpg', '').strip()
        data_extracao = row.get['data_extracao'] if pd.notna(row['data_extracao']) else timezone.now(),

        if not prontuario or not nome:
            erro_msg = f"❌ Erro: Prontuário ou Nome inválido. Linha: {row}"
            erros.append(erro_msg)
            print(erro_msg)
            continue

        try:
            # Verifica se o prontuário já existe no banco
            interno_existente = Interno.objects.filter(prontuario=prontuario).first()

            if interno_existente:
                # Atualiza os campos se houver alterações
                if (interno_existente.nome != nome or
                    interno_existente.cpf != cpf or
                    interno_existente.data_extracao != data_extracao):
                    interno_existente.nome = nome
                    interno_existente.cpf = cpf
                    interno_existente.data_extracao = data_extracao
                    atualizacoes.append(interno_existente)
            else:
                # Cria um novo registro
                novos_registros.append(Interno(
                    prontuario=prontuario,
                    nome=nome,
                    cpf=cpf,
                    data_extracao=data_extracao,
                ))

        except Exception as e:
            erro_msg = f"🔥 Erro ao processar registro {prontuario}: {str(e)}"
            erros.append(erro_msg)
            print(erro_msg)

    # Insere novos registros e atualiza os existentes
    try:
        with transaction.atomic():
            if novos_registros:
                Interno.objects.bulk_create(novos_registros)
                print(f"✅ {len(novos_registros)} novos registros inseridos.")
            if atualizacoes:
                Interno.objects.bulk_update(atualizacoes, ['nome', 'cpf', 'data_extracao'])
                print(f"✅ {len(atualizacoes)} registros atualizados.")
    except Exception as e:
        erro_msg = f"🔥 Erro ao salvar registros: {str(e)}"
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



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
        # Converte os valores para string e remove espaços em branco
        prontuario = str(row.get('prontuario', '')).strip()
        nome = str(row.get('nome', '')).strip()
        cpf = str(row.get('cpf', '')).strip()
        nome_mae = str(row.get('nome_mae', '')).strip()
        unidade = str(row.get('unidade', '')).strip()
        status = str(row.get('status', '')).strip()
        data_extracao = row.get('data_extracao', timezone.now()) if pd.notna(row.get('data_extracao', None)) else timezone.now()

        # Verifica se os campos obrigatórios estão preenchidos
        if not prontuario or not nome:
            erro_msg = f"❌ Erro: Prontuário ou Nome inválido. Linha: {row}"
            erros.append(erro_msg)
            print(erro_msg)
            continue

        try:
            # Verifica se o prontuário já existe no banco
            interno_existente = Interno.objects.filter(prontuario=prontuario).first()

            if interno_existente:
                # Verifica se algum dos outros campos foi alterado em relação ao que está no banco
                if (interno_existente.nome != nome or
                        interno_existente.cpf != cpf or
                        interno_existente.nome_mae != nome_mae or
                        interno_existente.unidade != unidade or
                        interno_existente.status != status):
                    # Atualiza apenas os campos que mudaram
                    interno_existente.nome = nome
                    interno_existente.cpf = cpf
                    interno_existente.nome_mae = nome_mae
                    interno_existente.unidade = unidade
                    interno_existente.status = status

                    # Se algum campo mudou, ATUALIZA data_extracao com a que veio da planilha
                    interno_existente.data_extracao = data_extracao

                    atualizacoes.append(interno_existente)

            else:
                # Cria um novo registro com a data de extração da planilha
                novos_registros.append(Interno(
                    prontuario=prontuario,
                    nome=nome,
                    cpf=cpf,
                    nome_mae=nome_mae,
                    unidade=unidade,
                    status=status,
                    data_extracao=data_extracao,  # Usa a data de extração da planilha para novos registros
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



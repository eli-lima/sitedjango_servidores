import pandas as pd
import requests
from .models import Interno
from celery import shared_task
from django.utils import timezone
from django.db import transaction
import traceback





@shared_task
def process_batch_internos(df_batch):
    novos_registros = []
    atualizacoes = []
    erros = []
    csv_log = "log_atualizacoes.csv"

    log_entries = []  # Lista para armazenar logs

    print(f"📌 Processando lote de {len(df_batch)} registros...")

    for row in df_batch:
        prontuario = str(row.get('prontuario', '')).strip()
        nome = str(row.get('nome', '')).strip()
        cpf = str(row.get('cpf', '')).strip()
        nome_mae = str(row.get('nome_mae', '')).strip()
        unidade = str(row.get('unidade', '')).strip()
        status = str(row.get('status', '')).strip()
        data_extracao = row.get('data_extracao', timezone.now()) if pd.notna(row.get('data_extracao', None)) else timezone.now()

        if not prontuario or not nome:
            erro_msg = f"❌ Erro: Prontuário ou Nome inválido. Linha: {row}"
            erros.append(erro_msg)
            print(erro_msg)
            continue

        try:
            interno = Interno.objects.filter(prontuario=prontuario).first()

            if interno:
                alterado = False
                campos_modificados = []

                if interno.nome != nome:
                    interno.nome = nome
                    campos_modificados.append("nome")
                    alterado = True

                if interno.cpf != cpf:
                    interno.cpf = cpf
                    campos_modificados.append("cpf")
                    alterado = True

                if interno.nome_mae != nome_mae:
                    interno.nome_mae = nome_mae
                    campos_modificados.append("nome_mae")
                    alterado = True

                if interno.unidade != unidade:
                    interno.unidade = unidade
                    campos_modificados.append("unidade")
                    alterado = True

                if interno.status != status:
                    interno.status = status
                    campos_modificados.append("status")
                    alterado = True

                if alterado:
                    interno.data_extracao = data_extracao
                    campos_modificados.append("data_extracao")
                    atualizacoes.append(interno)

                    log_entries.append([prontuario, ", ".join(campos_modificados), str(timezone.now())])

            else:
                novos_registros.append(Interno(
                    prontuario=prontuario,
                    nome=nome,
                    cpf=cpf,
                    nome_mae=nome_mae,
                    unidade=unidade,
                    status=status,
                    data_extracao=data_extracao,
                ))
                log_entries.append([prontuario, "Novo Registro", str(timezone.now())])

        except Exception as e:
            erro_msg = f"🔥 Erro ao processar registro {prontuario}: {str(e)}"
            erros.append(erro_msg)
            print(erro_msg)

    novos_count = len(novos_registros)
    atualizados_count = len(atualizacoes)

    try:
        with transaction.atomic():
            if novos_registros:
                Interno.objects.bulk_create(novos_registros)
                print(f"✅ {novos_count} novos registros inseridos.")
            if atualizacoes:
                Interno.objects.bulk_update(atualizacoes, ['nome', 'cpf', 'data_extracao'])
                print(f"✅ {atualizados_count} registros atualizados.")
    except Exception as e:
        erro_msg = f"🔥 Erro ao salvar registros: {str(e)}"
        erros.append(erro_msg)
        print(erro_msg)

    print(f"📝 Salvando log em CSV no arquivo {csv_log}")
    log_df = pd.DataFrame(log_entries, columns=["Prontuario", "Campos Modificados", "Data"])
    log_df.to_csv(csv_log, mode="a", header=False, index=False)

    print("✅ Atualização concluída!")

    return {'erros': erros, 'novos_count': novos_count, 'atualizados_count': atualizados_count}





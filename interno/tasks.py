import pandas as pd
import requests
from .models import Interno
from celery import shared_task
from django.utils import timezone
from django.db import transaction
import traceback
from datetime import datetime
import os


@shared_task
def process_batch_internos(df_batch):
    novos_registros = []
    atualizacoes = []  # Lista para armazenar objetos Interno que serão atualizados
    campos_para_atualizar = ['nome', 'cpf', 'nome_mae', 'unidade', 'status', 'data_extracao']
    erros = []
    csv_log = "log_atualizacoes.csv"

    log_entries = []  # Lista para armazenar logs

    print(f"📌 Processando lote de {len(df_batch)} registros...")

    for row in df_batch:
        prontuario = str(row.get('prontuario', '')).strip()
        nome = str(row.get('nome', '')).strip()
        cpf = str(row.get('cpf', '')).strip()
        nome_mae = str(row.get('nome_mae', '')).strip()

        unidade = row.get('unidade', '')
        if pd.isna(unidade) or unidade == 'nan':
            unidade = ''
        else:
            unidade = str(unidade).strip()

        status = str(row.get('status', '')).strip()
        data_extracao = row.get('data_extracao')
        if not data_extracao or pd.isna(data_extracao):
            data_extracao = timezone.now()
        else:
            try:
                data_extracao = datetime.strptime(data_extracao, "%d-%m-%Y").date()
            except ValueError:
                raise ValueError(f"Data inválida: {data_extracao}")

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

                # Verifica e atualiza cada campo
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
                    atualizacoes.append(interno)  # Adiciona o objeto Interno à lista de atualizações
                    log_entries.append([prontuario, ", ".join(campos_modificados), str(timezone.now())])

            else:
                novo_interno = Interno(
                    prontuario=prontuario,
                    nome=nome,
                    cpf=cpf,
                    nome_mae=nome_mae,
                    unidade=unidade,
                    status=status,
                    data_extracao=data_extracao,
                )
                novos_registros.append(novo_interno)
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
                # Usamos bulk_update com os campos específicos
                Interno.objects.bulk_update(atualizacoes, campos_para_atualizar)
                print(f"✅ {atualizados_count} registros atualizados.")
    except Exception as e:
        erro_msg = f"🔥 Erro ao salvar registros: {str(e)}"
        erros.append(erro_msg)
        print(erro_msg)

    print(f"📝 Salvando log em CSV no arquivo {csv_log}")

    try:
        log_df = pd.DataFrame(log_entries, columns=["Prontuario", "Campos Modificados", "Data"])

        # Se o arquivo já existe, salva sem o cabeçalho
        if os.path.exists(csv_log):
            log_df.to_csv(csv_log, mode="a", header=False, index=False)
        else:
            log_df.to_csv(csv_log, mode="w", header=True, index=False)
    except Exception as e:
        erro_msg = f"🔥 Erro ao salvar log: {str(e)}"
        erros.append(erro_msg)
        print(erro_msg)

    print("✅ Atualização concluída!")

    return {'erros': erros, 'novos_count': novos_count, 'atualizados_count': atualizados_count}



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
        total_novos = 0
        total_atualizados = 0

        for start in range(0, len(df), batch_size):
            df_batch = df.iloc[start:start + batch_size].to_dict(orient='records')
            print(f"🚀 Enviando lote {start // batch_size + 1} para processamento...")
            resultado = process_batch_internos(df_batch)

            erros_totais.extend(resultado['erros'])
            total_novos += resultado['novos_count']
            total_atualizados += resultado['atualizados_count']

        print(f"✅ Processamento concluído. Total de erros: {len(erros_totais)}")
        print(f"📌 Total de novos registros: {total_novos}")
        print(f"📌 Total de registros atualizados: {total_atualizados}")

        return {
            'status': 'sucesso' if not erros_totais else 'erro',
            'erros': erros_totais,
            'total_novos': total_novos,
            'total_atualizados': total_atualizados
        }
    except Exception as e:
        erro_msg = f"🔥 Erro geral no processamento: {str(e)}\n{traceback.format_exc()}"
        print(erro_msg)
        return {'status': 'falha', 'mensagem': erro_msg}




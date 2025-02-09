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
        # Tratando a unidade para garantir que valores 'NaN' sejam tratados corretamente
        unidade = row.get('unidade', '')  # Atribui valor vazio se não encontrar o campo
        if pd.isna(unidade) or unidade == 'nan':  # Verifica se é NaN ou 'nan'
            unidade = ''  # Substitui por string vazia

        else:
            unidade = str(unidade).strip()  # Converte para string e remove espaços, caso contrário
        status = str(row.get('status', '')).strip()
        data_extracao = row.get('data_extracao')
        if not data_extracao or pd.isna(data_extracao):
            data_extracao = timezone.now()

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
                Interno.objects.bulk_update(atualizacoes, ['nome', 'cpf', 'nome_mae', 'unidade', 'status', 'data_extracao'])
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




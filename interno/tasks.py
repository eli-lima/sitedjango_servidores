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
            interno = Interno.objects.filter(prontuario=prontuario).first()

            if interno:
                # Verifica se algum dos outros campos foi alterado em relação ao que está no banco
                print(f"🔄 Interno encontrado: {interno}")
                # Comparar campos para ver se há mudanças
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

                # Só atualiza a `data_extracao` se algum outro campo mudou
                if alterado:
                    interno.data_extracao = data_extracao
                    campos_modificados.append("data_extracao")

                    atualizacoes.append(interno)
                    # Criar log
                    log_entries.append(
                        [prontuario, ", ".join(campos_modificados), str(timezone.now())])


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
                # Criar log de novo registro
                log_entries.append([prontuario, "Novo Registro", str(timezone.now())])



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

    # Salvar log em CSV
    print(f"📝 Salvando log em CSV no arquivo {csv_log}")
    log_df = pd.DataFrame(log_entries, columns=["Prontuario", "Campos Modificados", "Data"])
    log_df.to_csv(csv_log, mode="a", header=False, index=False)

    print("✅ Atualização concluída!")

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
        # Captura o erro e inclui o traceback completo
        erro_msg = f"🔥 Erro geral no processamento: {str(e)}\n{traceback.format_exc()}"
        print(erro_msg)  # Aqui você imprime o erro no log de execução
        return {'status': 'falha', 'mensagem': erro_msg}




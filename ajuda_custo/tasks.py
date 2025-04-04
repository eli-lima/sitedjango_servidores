from .models import Ajuda_Custo, DataMajorada
from servidor.models import Servidor
from datetime import timedelta
from django.db import IntegrityError
from dateutil import parser
import re
import pandas as pd
from celery import shared_task
import requests
from collections import defaultdict
from datetime import datetime


@shared_task
def process_batch(df_batch):
    registros_inseridos = 0
    ajuda_custos_para_inserir = []
    horas_por_servidor_mes = defaultdict(int)
    erros = []

    print("\n=== INÍCIO DO PROCESSAMENTO ===")
    print(f"Total de registros a processar: {len(df_batch)}")

    # 1. Coleta de dados únicos
    servidores_no_lote = set()
    meses_anos_no_lote = set()

    for i, row in enumerate(df_batch, 1):
        try:
            matricula = int(re.sub(r'\D', '', str(row['Matrícula'])).lstrip('0'))
            data_completa = parser.parse(str(row['Data'])).date()
            servidores_no_lote.add(matricula)
            meses_anos_no_lote.add((data_completa.year, data_completa.month))
        except Exception as e:
            error_message = f"ERRO no registro {i} (inicialização): {str(e)}"
            print(error_message)
            erros.append(error_message)
            continue

    # 2. Consulta ao banco
    if servidores_no_lote and meses_anos_no_lote:
        registros_banco = Ajuda_Custo.objects.filter(
            matricula__in=servidores_no_lote,
            data__year__in=[ano for ano, mes in meses_anos_no_lote],
            data__month__in=[mes for ano, mes in meses_anos_no_lote]
        )

        for registro in registros_banco:
            key = (registro.matricula, registro.data.year, registro.data.month)
            horas_por_servidor_mes[key] += 12 if registro.carga_horaria.strip() == "12 horas" else 24

    # 3. Processamento do lote
    for i, row in enumerate(df_batch, 1):
        try:
            print(f"\n--- Processando registro {i} ---")
            matricula = int(re.sub(r'\D', '', str(row['Matrícula'])).lstrip('0'))
            nome = row['Nome']
            data_completa = parser.parse(str(row['Data'])).date()
            mes_ano_key = (matricula, data_completa.year, data_completa.month)
            carga_horaria = 12 if str(row['Carga Horaria']).strip() == "12 horas" else 24

            print(f"Servidor: {nome} (Matrícula: {matricula})")
            print(f"Data: {data_completa.strftime('%d/%m/%Y')} | Carga: {carga_horaria}h")

            # Verificação de registro existente
            if Ajuda_Custo.objects.filter(matricula=matricula, data=data_completa).exists():
                error_message = f"REGISTRO DUPLICADO: {nome} em {data_completa.strftime('%d/%m/%Y')}"
                print(error_message)
                erros.append(error_message)
                continue

            # Cálculo de horas
            horas_banco = horas_por_servidor_mes.get(mes_ano_key, 0)
            horas_lote = sum(
                12 if r.carga_horaria.strip() == "12 horas" else 24
                for r in ajuda_custos_para_inserir
                if (r.matricula, r.data.year, r.data.month) == mes_ano_key
            )
            total_horas = horas_banco + horas_lote + carga_horaria

            print("\nDEBUG - CÁLCULO DE HORAS:")
            print(f"Banco: {horas_banco}h | Lote: {horas_lote}h | Atual: {carga_horaria}h")
            print(f"TOTAL: {total_horas}h (Limite: 192h)")

            if total_horas > 192:
                error_message = f"LIMITE EXCEDIDO: {nome} ({matricula}) - {total_horas}h em {data_completa.strftime('%m/%Y')}"
                print(error_message)
                erros.append(error_message)
                continue

            # Adição ao lote
            ajuda_custos_para_inserir.append(Ajuda_Custo(
                matricula=matricula,
                nome=nome,
                data=data_completa,
                unidade=row['Unidade'],
                carga_horaria=row['Carga Horaria'],
                majorado=DataMajorada.objects.filter(data=data_completa).exists()
            ))
            print("✅ Registro válido - Adicionado ao lote")

        except Exception as e:
            error_message = f"ERRO NO PROCESSAMENTO (registro {i}): {str(e)}"
            print(error_message)
            erros.append(error_message)
            continue

    # 4. Inserção final
    print("\n=== ETAPA FINAL ===")
    print(f"Total a inserir: {len(ajuda_custos_para_inserir)}")
    print(f"Total de erros: {len(erros)}")

    if ajuda_custos_para_inserir:
        try:
            Ajuda_Custo.objects.bulk_create(ajuda_custos_para_inserir)
            registros_inseridos = len(ajuda_custos_para_inserir)
            print("✅ Inserção em lote concluída com sucesso")
        except Exception as e:
            error_message = f"FALHA NA INSERÇÃO: {str(e)}"
            print(error_message)
            erros.append(error_message)

    return {
        'status': 'sucesso' if registros_inseridos > 0 and not erros else 'erro',
        'registros_inseridos': registros_inseridos,
        'total_erros': len(erros),
        'erros': erros[:100]  # Limita a 100 erros
    }


@shared_task(bind=True)
def process_excel_file(self, cloudinary_url):

    try:
        # Fazer o download do arquivo do Cloudinary
        response = requests.get(cloudinary_url)
        response.raise_for_status()


        # Ler o arquivo Excel
        df = pd.read_excel(response.content)


        # Lógica de processamento dos dados
        batch_size = 10000
        total_registros = df.shape[0]
        print(f"Total de registros a processar: {total_registros}")
        erros_totais = []

        for start in range(0, total_registros, batch_size):
            end = min(start + batch_size, total_registros)
            df_batch = df.iloc[start:end]

            # Converte o batch para uma lista de dicionários
            df_batch_dict = df_batch.to_dict(orient='records')
            print(f"Processando lote de registros: {start} a {end}")

            # Processa o lote e acumula erros
            result = process_batch(df_batch_dict)  # Chama a função que já processa os dados
            erros_totais.extend(result)

        print(f"Processamento concluído. Erros totais: {len(erros_totais)}")

        # Retorna status e erros, se houver
        return {'status': 'sucesso' if not erros_totais else 'erro', 'erros': erros_totais}

    except Exception as e:
        print(f"Ocorreu um erro durante o processamento: {str(e)}")  # Print do erro
        return {'status': 'falha', 'mensagem': str(e)}

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
    horas_por_servidor_mes = defaultdict(int)  # (matricula, ano, mes) -> horas
    erros = []

    print("\n=== INÍCIO DO PROCESSAMENTO DO LOTE ===\n")
    print(f"Total de registros no lote: {len(df_batch)}")

    # 1. Coleta todas as matrículas e meses/anos únicos no lote
    servidores_no_lote = set()
    meses_anos_no_lote = set()

    for row in df_batch:
        try:
            matricula = int(re.sub(r'\D', '', str(row['Matrícula'])).lstrip('0'))
            data_completa = parser.parse(str(row['Data'])).date()
            servidores_no_lote.add(matricula)
            meses_anos_no_lote.add((data_completa.year, data_completa.month))
        except Exception as e:
            erros.append(f"Erro ao extrair matrícula/data: {str(e)}")
            continue

    print(f"\nServidores únicos no lote: {servidores_no_lote}")
    print(f"Meses/anos únicos no lote: {meses_anos_no_lote}")

    # 2. Consulta as horas já registradas no banco
    if servidores_no_lote and meses_anos_no_lote:
        print("\nConsultando horas existentes no banco...")
        registros_banco = Ajuda_Custo.objects.filter(
            matricula__in=servidores_no_lote,
            data__year__in=[ano for ano, mes in meses_anos_no_lote],
            data__month__in=[mes for ano, mes in meses_anos_no_lote]
        )
        print(f"Total de registros existentes encontrados: {registros_banco.count()}")

        for registro in registros_banco:
            key = (registro.matricula, registro.data.year, registro.data.month)
            horas = 12 if registro.carga_horaria.strip() == "12 horas" else 24
            horas_por_servidor_mes[key] += horas
            print(
                f"  - {registro.matricula} {registro.data.strftime('%m/%Y')}: +{horas}h (Total: {horas_por_servidor_mes[key]}h)")

    # 3. Processa o lote atual
    print("\nProcessando registros do lote atual...")
    for i, row in enumerate(df_batch, 1):
        try:
            print(f"\n--- Registro {i} ---")
            # Processamento básico
            matricula = int(re.sub(r'\D', '', str(row['Matrícula'])).lstrip('0'))
            nome = row['Nome']
            data_completa = parser.parse(str(row['Data'])).date()
            mes_ano_key = (matricula, data_completa.year, data_completa.month)
            carga_horaria = 12 if str(row['Carga Horaria']).strip() == "12 horas" else 24

            print(f"Servidor: {nome} (Matrícula: {matricula})")
            print(f"Data: {data_completa.strftime('%d/%m/%Y')} | Carga: {carga_horaria}h")

            # Verifica registro existente
            if Ajuda_Custo.objects.filter(matricula=matricula, data=data_completa).exists():
                msg = f"REGISTRO JÁ EXISTE: {nome} em {data_completa.strftime('%d/%m/%Y')}"
                print(msg)
                erros.append(msg)
                continue

            # Calcula totais
            horas_banco = horas_por_servidor_mes.get(mes_ano_key, 0)
            horas_lote_atual = sum(
                12 if r.carga_horaria.strip() == "12 horas" else 24
                for r in ajuda_custos_para_inserir
                if (r.matricula, r.data.year, r.data.month) == mes_ano_key
            )
            horas_totais = horas_banco + horas_lote_atual

            print("\nDEBUG - CÁLCULO DE HORAS:")
            print(f"  - Banco de dados: {horas_banco}h")
            print(f"  - Lote atual: {horas_lote_atual}h")
            print(f"  - Registro atual: {carga_horaria}h")
            print(f"  - TOTAL PARCIAL: {horas_totais}h")
            print(f"  - TOTAL + ATUAL: {horas_totais + carga_horaria}h (Limite: 192h)")

            # Verificação do limite
            if (horas_totais + carga_horaria) > 192:
                msg = (f"LIMITE EXCEDIDO: {nome} (Matrícula: {matricula}) "
                       f"em {data_completa.strftime('%m/%Y')} - "
                       f"Total: {horas_totais + carga_horaria}h (Limite: 192h)")
                print(msg)
                erros.append(msg)
                continue

            print("✅ Dentro do limite - Adicionando ao lote")

            # Adiciona ao lote de inserção
            ajuda_custos_para_inserir.append(Ajuda_Custo(
                matricula=matricula,
                nome=nome,
                data=data_completa,
                unidade=row['Unidade'],
                carga_horaria=row['Carga Horaria'],
                majorado=DataMajorada.objects.filter(data=data_completa).exists()
            ))

        except Exception as e:
            msg = f"ERRO NO REGISTRO {i}: {str(e)}"
            print(msg)
            erros.append(msg)
            continue

    # 4. Insere tudo de uma vez
    print("\n=== RESUMO FINAL ===")
    print(f"Registros válidos para inserção: {len(ajuda_custos_para_inserir)}")
    print(f"Total de erros detectados: {len(erros)}")

    if ajuda_custos_para_inserir:
        try:
            print("Iniciando inserção em lote...")
            Ajuda_Custo.objects.bulk_create(ajuda_custos_para_inserir)
            registros_inseridos = len(ajuda_custos_para_inserir)
            print(f"✅ {registros_inseridos} registros inseridos com sucesso")
        except Exception as e:
            msg = f"ERRO NA INSERÇÃO EM LOTE: {str(e)}"
            print(msg)
            erros.append(msg)

    return {
        'registros_inseridos': registros_inseridos,
        'total_erros': len(erros),
        'erros': erros[:100]  # Limita a 100 erros para evitar payload muito grande
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

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
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


@shared_task
def process_batch(df_batch):
    print("=== INÍCIO DO PROCESS_BATCH ===")
    registros_inseridos = 0
    ajuda_custos_para_inserir = []
    horas_por_servidor_mes = defaultdict(int)
    erros = []

    print(f"Tipo do df_batch: {type(df_batch)}")  # Debug
    print(f"Colunas disponíveis: {df_batch.columns.tolist() if hasattr(df_batch, 'columns') else 'N/A'}")  # Debug

    # 1. Coleta de dados únicos
    servidores_no_lote = set()
    meses_anos_no_lote = set()
    print("Iniciando coleta de dados únicos...")  # Debug

    for i, row in df_batch.iterrows():
        try:
            print(f"\nProcessando linha {i + 1}")  # Debug
            matricula_str = str(row['Matrícula'])
            print(f"Matrícula original: {matricula_str}")  # Debug
            matricula = int(re.sub(r'\D', '', matricula_str).lstrip('0'))
            print(f"Matrícula processada: {matricula}")  # Debug

            data_str = str(row['Data'])
            print(f"Data original: {data_str}")  # Debug
            data_completa = parser.parse(data_str).date()
            print(f"Data processada: {data_completa}")  # Debug

            servidores_no_lote.add(matricula)
            meses_anos_no_lote.add((data_completa.year, data_completa.month))

        except Exception as e:
            error_message = f"ERRO no registro {i + 1} (inicialização): {str(e)}"
            print(error_message)  # Debug
            erros.append(error_message)
            continue

    print(f"\nServidores únicos encontrados: {servidores_no_lote}")  # Debug
    print(f"Meses/anos únicos encontrados: {meses_anos_no_lote}")  # Debug

    # 2. Consulta ao banco
    if servidores_no_lote and meses_anos_no_lote:
        print("\nConsultando banco de dados...")  # Debug
        registros_banco = Ajuda_Custo.objects.filter(
            matricula__in=servidores_no_lote,
            data__year__in=[ano for ano, mes in meses_anos_no_lote],
            data__month__in=[mes for ano, mes in meses_anos_no_lote]
        )
        print(f"Registros encontrados no banco: {registros_banco.count()}")  # Debug

        for registro in registros_banco:
            key = (registro.matricula, registro.data.year, registro.data.month)
            horas = 12 if registro.carga_horaria.strip() == "12 horas" else 24
            horas_por_servidor_mes[key] += horas
            print(f"Registro banco: {registro.matricula} - {registro.data}: {horas}h")  # Debug

    # 3. Processamento do lote
    print("\nIniciando processamento do lote...")  # Debug
    for i, row in df_batch.iterrows():
        try:
            print(f"\n--- Processando registro {i + 1} ---")  # Debug

            # Processa matrícula
            matricula_str = str(row['Matrícula'])
            matricula = int(re.sub(r'\D', '', matricula_str).lstrip('0'))
            nome = row['Nome']
            print(f"Servidor: {nome} (Matrícula: {matricula})")  # Debug

            # Processa data
            data_str = str(row['Data'])
            data_completa = parser.parse(data_str).date()
            print(f"Data: {data_completa.strftime('%d/%m/%Y')}")  # Debug

            # Processa carga horária
            carga_horaria_str = str(row['Carga Horaria']).strip()
            carga_horaria = 12 if carga_horaria_str == "12 horas" else 24
            print(f"Carga horária: {carga_horaria}h")  # Debug

            # Verificação de registro existente
            if Ajuda_Custo.objects.filter(matricula=matricula, data=data_completa).exists():
                error_message = f"REGISTRO DUPLICADO: {nome} em {data_completa.strftime('%d/%m/%Y')}"
                print(error_message)  # Debug
                erros.append(error_message)
                continue

            # Cálculo de horas
            mes_ano_key = (matricula, data_completa.year, data_completa.month)
            horas_banco = horas_por_servidor_mes.get(mes_ano_key, 0)

            horas_lote = sum(
                12 if r.carga_horaria.strip() == "12 horas" else 24
                for r in ajuda_custos_para_inserir
                if (r.matricula, r.data.year, r.data.month) == mes_ano_key
            )

            total_horas = horas_banco + horas_lote + carga_horaria
            print(f"\nDEBUG - CÁLCULO DE HORAS:")
            print(f"Banco: {horas_banco}h | Lote: {horas_lote}h | Atual: {carga_horaria}h")
            print(f"TOTAL: {total_horas}h (Limite: 192h)")

            if total_horas > 192:
                error_message = f"LIMITE EXCEDIDO: {nome} ({matricula}) - {total_horas}h em {data_completa.strftime('%m/%Y')}"
                print(error_message)  # Debug
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
            print("✅ Registro válido - Adicionado ao lote")  # Debug

        except Exception as e:
            error_message = f"ERRO NO PROCESSAMENTO (registro {i + 1}): {str(e)}"
            print(error_message)  # Debug
            erros.append(error_message)
            continue

    # 4. Inserção final
    print("\n=== ETAPA FINAL ===")
    print(f"Total a inserir: {len(ajuda_custos_para_inserir)}")
    print(f"Total de erros: {len(erros)}")

    if ajuda_custos_para_inserir:
        try:
            print("Iniciando bulk_create...")  # Debug
            with transaction.atomic():
                Ajuda_Custo.objects.bulk_create(ajuda_custos_para_inserir)
                registros_inseridos = len(ajuda_custos_para_inserir)
                print(f"✅ Inserção em lote concluída: {registros_inseridos} registros")  # Debug
        except Exception as e:
            error_message = f"FALHA NA INSERÇÃO: {str(e)}"
            print(error_message)  # Debug
            erros.append(error_message)

    print("\n=== RESUMO FINAL ===")
    print(
        f"Status: {'sucesso' if registros_inseridos > 0 else 'parcial' if registros_inseridos > 0 and erros else 'erro'}")
    print(f"Registros inseridos: {registros_inseridos}")
    print(f"Total de erros: {len(erros)}")

    return {
        'status': 'sucesso' if registros_inseridos > 0 else 'parcial' if registros_inseridos > 0 and erros else 'erro',
        'registros_inseridos': registros_inseridos,
        'total_erros': len(erros),
        'erros': erros[:100]
    }


@shared_task(bind=True)
def process_excel_file(self, cloudinary_url):
    print("\n=== INÍCIO DO PROCESS_EXCEL_FILE ===")
    print(f"URL do arquivo: {cloudinary_url}")  # Debug

    try:
        # Fazer o download do arquivo do Cloudinary
        print("Fazendo download do arquivo...")  # Debug
        response = requests.get(cloudinary_url)
        response.raise_for_status()
        print("Download concluído")  # Debug

        # Ler o arquivo Excel
        print("Lendo arquivo Excel...")  # Debug
        df = pd.read_excel(response.content)
        print(f"Total de linhas: {len(df)}")  # Debug

        # Verificar colunas necessárias
        colunas_necessarias = ['Matrícula', 'Nome', 'Data', 'Unidade', 'Carga Horaria']
        print(f"Colunas encontradas: {df.columns.tolist()}")  # Debug

        if not all(col in df.columns for col in colunas_necessarias):
            missing = [col for col in colunas_necessarias if col not in df.columns]
            error_msg = f"Colunas faltando no arquivo: {missing}"
            print(error_msg)  # Debug
            raise ValueError(error_msg)

        total_registros = len(df)
        print(f"Total de registros a processar: {total_registros}")  # Debug

        # Variáveis para resultados
        registros_inseridos_totais = 0
        erros_totais = []

        batch_size = 1000
        print(f"Tamanho do lote: {batch_size}")  # Debug

        for start in range(0, total_registros, batch_size):
            end = min(start + batch_size, total_registros)
            df_batch = df.iloc[start:end]
            print(f"\nProcessando lote: {start} a {end}")  # Debug

            result = process_batch(df_batch)
            print(f"Resultado do lote: {result}")  # Debug

            # Acumula resultados
            registros_inseridos_totais += result['registros_inseridos']
            erros_totais.extend(result['erros'])

            # Atualiza progresso
            progresso = int((end / total_registros) * 100)
            print(f"Progresso: {progresso}%")  # Debug

            self.update_state(
                state='PROGRESS',
                meta={
                    'processados': end,
                    'total': total_registros,
                    'inseridos': registros_inseridos_totais,
                    'erros': len(erros_totais),
                    'progresso': progresso
                }
            )

        print("\n=== PROCESSAMENTO CONCLUÍDO ===")
        print(f"Total inserido: {registros_inseridos_totais}")
        print(f"Total de erros: {len(erros_totais)}")

        status = 'sucesso' if registros_inseridos_totais > 0 and not erros_totais else 'parcial' if registros_inseridos_totais > 0 else 'erro'
        print(f"Status final: {status}")  # Debug

        return {
            'status': status,
            'registros_inseridos': registros_inseridos_totais,
            'total_erros': len(erros_totais),
            'erros': erros_totais[:100]
        }

    except Exception as e:
        error_msg = f"ERRO NO PROCESSAMENTO: {str(e)}"
        print(f"ERRO CRÍTICO: {error_msg}")  # Debug
        return {
            'status': 'falha',
            'mensagem': error_msg,
            'erros': [error_msg]
        }
from .models import Ajuda_Custo, DataMajorada
from servidor.models import Servidor

import pandas as pd
from celery import shared_task
import requests
from django.db.utils import IntegrityError
from collections import defaultdict
from dateutil import parser
import re
from django.db.models import IntegerField, Sum
from django.db.models.functions import Cast, Substr



@shared_task
def process_batch(df_batch):
    registros_inseridos = False
    ajuda_custos_para_inserir = []
    erros = []

    # Passo 1: Extraia os meses e anos únicos da planilha
    meses_anos_planilha = set()
    for row in df_batch:
        try:
            data = parser.parse(str(row['Data'])).date()  # Converte para a data sem horário
            print(data)
            meses_anos_planilha.add((data.year, data.month))
        except ValueError:
            erros.append(f"Erro: Data inválida {row['Data']} encontrada.")
            continue

    # Passo 2: Obtenha as horas acumuladas no banco de dados filtrando pelos meses e anos da planilha
    horas_acumuladas_banco = defaultdict(int)
    registros_db = (
        Ajuda_Custo.objects
        .filter(
            data__year__in={ano for ano, mes in meses_anos_planilha},
            data__month__in={mes for ano, mes in meses_anos_planilha}
        )
        .annotate(
            carga_horaria_num=Cast(Substr('carga_horaria', 1, 2), IntegerField())  # Extraindo horas numéricas
        )
        .values('matricula', 'data__year', 'data__month')
        .annotate(total_horas=Sum('carga_horaria_num'))
    )

    # Carrega as horas acumuladas do banco em um dicionário
    for registro in registros_db:
        matricula = registro['matricula']
        mes_ano = (registro['data__year'], registro['data__month'])
        horas_acumuladas_banco[(matricula, mes_ano)] += registro['total_horas']

    # Passo 3: Verificação e processamento dos dados da planilha
    datas_processadas = set()

    for row in df_batch:
        matricula_raw = row['Matrícula']
        if not matricula_raw:
            erros.append("Erro: Matrícula vazia encontrada.")
            continue

        matricula = re.sub(r'\D', '', str(matricula_raw)).lstrip('0')
        unidade = row['Unidade']
        nome = row['Nome']
        data = row['Data']
        carga_horaria_raw = row['Carga Horaria']

        # Converte a carga horária de texto para número inteiro
        carga_horaria = 0
        if carga_horaria_raw.strip() == "12 horas":
            carga_horaria = 12
        elif carga_horaria_raw.strip() == "24 horas":
            carga_horaria = 24
        else:
            erros.append(f"Erro: Carga horária inválida '{carga_horaria_raw}' para o servidor {nome}.")
            continue

        try:
            servidor = Servidor.objects.get(matricula=matricula)
        except Servidor.DoesNotExist:
            erros.append(f"Erro: Servidor com matrícula {matricula} não encontrado.")
            continue

        try:
            data_completa = parser.parse(data).date()
        except ValueError:
            erros.append(f"Erro: Data inválida {data} para o servidor {nome}.")
            continue

        # Verificar se a data já foi processada neste lote
        if (servidor.matricula, data_completa) in datas_processadas:
            erros.append(f"Registro duplicado para o servidor {nome} na data {data_completa}.")
            continue

        # Verificar no banco de dados se já existe um registro para a mesma matrícula e data
        if Ajuda_Custo.objects.filter(matricula=servidor.matricula, data=data_completa).exists():
            erros.append(f"Erro: Registro já existe para o servidor {nome} na data {data_completa}.")
            continue

        datas_processadas.add((servidor.matricula, data_completa))

        # Extraindo mês e ano da data
        mes_ano = (data_completa.year, data_completa.month)

        # Adicionar a carga horária do registro atual ao somatório do banco
        horas_mes_ano = horas_acumuladas_banco[(servidor.matricula, mes_ano)] + carga_horaria

        # Verificar se o limite de 192 horas foi ultrapassado
        if horas_mes_ano > 192:
            erros.append(
                f"Limite de 192 horas excedido para o servidor {nome} no mês {data_completa.strftime('%m/%Y')}.")
            continue

        # Atualizar o somatório de horas no dicionário
        horas_acumuladas_banco[(servidor.matricula, mes_ano)] = horas_mes_ano

        majorado = DataMajorada.objects.filter(data=data_completa).exists()

        ajuda_custos_para_inserir.append(Ajuda_Custo(
            matricula=servidor.matricula,
            nome=servidor.nome,
            data=data_completa,
            unidade=unidade,
            carga_horaria=carga_horaria_raw,
            majorado=majorado
        ))

    # Inserir dados em massa, se não houver erros
    if not erros and ajuda_custos_para_inserir:
        try:
            Ajuda_Custo.objects.bulk_create(ajuda_custos_para_inserir)
            registros_inseridos = True
        except IntegrityError as e:
            erros.append(f"Erro de integridade durante a inserção: {str(e)}")

    if registros_inseridos:
        print("Registros inseridos com sucesso!")
    else:
        print("Nenhum registro foi inserido.")

    if erros:
        print("Erros encontrados:")
        for erro in erros:
            print(erro)

    return erros  # Retorna a lista de erros para feedback



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

        erros_totais = []

        for start in range(0, total_registros, batch_size):
            end = min(start + batch_size, total_registros)
            df_batch = df.iloc[start:end]

            # Converte o batch para uma lista de dicionários
            df_batch_dict = df_batch.to_dict(orient='records')


            # Processa o lote e acumula erros
            result = process_batch(df_batch_dict)  # Chama a função que já processa os dados
            erros_totais.extend(result)

        print(f"Processamento concluído. Erros totais: {len(erros_totais)}")

        # Retorna status e erros, se houver
        return {'status': 'sucesso' if not erros_totais else 'erro', 'erros': erros_totais}

    except Exception as e:

        return {'status': 'falha', 'mensagem': str(e)}

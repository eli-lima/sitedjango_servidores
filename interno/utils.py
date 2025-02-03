import pdfplumber
import re
from datetime import datetime
from .models import Interno


def extrair_dados_pdf(caminho_pdf):
    dados = []
    with pdfplumber.open(caminho_pdf) as pdf:
        unidade = None
        data_extracao = None
        status = None  # Variável para identificar o status do PDF

        for page in pdf.pages:
            texto = page.extract_text()

            # Determinar o status (ativo ou inativo)
            if not status:
                status_match = re.search(r'Status: (\w);', texto)
                if status_match:
                    status = status_match.group(1)

            # Extrair a unidade prisional apenas se o status for "A" (ativo)
            if not unidade and status == "A":
                unidade_match = re.search(r'Unidade Prisional: (.+?);', texto)
                if unidade_match:
                    unidade = unidade_match.group(1)

            # Extrair a data de geração
            if not data_extracao:
                data_match = re.search(r'Gerado em (\d{2}/\d{2}/\d{4})', texto)
                if data_match:
                    data_extracao = datetime.strptime(data_match.group(1), '%d/%m/%Y').date()

            # Extrair os dados dos internos
            linhas = re.findall(r'\d+- \((\d+)\) - (.+?) - (.+?) - (.+)', texto)
            for linha in linhas:
                prontuario, nome, cpf, nome_mae = linha
                cpf = cpf.strip() if cpf != '-' else None
                nome_mae = nome_mae.strip() if nome_mae != '-' else None
                dados.append({
                    'prontuario': prontuario.strip(),
                    'nome': nome.strip(),
                    'cpf': cpf,
                    'nome_mae': nome_mae,
                    'unidade': unidade if status == "A" else None,  # Unidade só para ativos
                    'status': "Ativo" if status == "A" else "Inativo",  # Adicionar status
                    'data_extracao': data_extracao,
                })
    return dados



def salvar_dados(dados):
    for interno in dados:
        Interno.objects.update_or_create(
            prontuario=interno['prontuario'],
            defaults={
                'nome': interno['nome'],
                'cpf': interno['cpf'],
                'nome_mae': interno['nome_mae'],
                'unidade': interno['unidade'],  # Pode ser None para inativos
                'status': interno['status'],  # Incluímos o status
                'data_extracao': interno['data_extracao'],
            }
        )

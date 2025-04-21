import pdfplumber
import re
from datetime import datetime
from .models import Interno





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

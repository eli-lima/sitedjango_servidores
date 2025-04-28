# core/utils.py (ou apps/seu_app/utils.py)
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from .models import Unidade
from servidor.models import Servidor


def get_unidade_choices():
    # Mova a lógica de consulta para uma função separada
    return [('', '--- Selecione uma unidade ---')] + [(u.nome, u.nome) for u in Unidade.objects.all().order_by('nome')]


MESES_PT_BR = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}


def get_nome_mes(numero_mes):
    """Retorna o nome do mês em português"""
    return MESES_PT_BR.get(numero_mes, f"Mês {numero_mes}")


def get_periodo_12_meses(mes_referencia, ano_referencia):
    """
    Retorna uma lista de 12 meses anteriores ao mês/ano de referência
    no formato [(ano, mês, nome_mês), ...]
    """
    periodo = []
    data_referencia = datetime(year=ano_referencia, month=mes_referencia, day=1)

    for i in range(12):
        data = data_referencia - relativedelta(months=i)
        periodo.append((data.year, data.month, get_nome_mes(data.month)))

    # Inverte para começar do mais antigo para o mais recente
    return periodo[::-1]


def get_servidor_for_view(view):
    """
    Versão adaptada para class-based views que mantém a função original intacta
    """
    try:
        # Usa a função original passando o request da view
        return get_servidor(view.request)
    except Exception as e:
        # Adiciona a mensagem de erro ao sistema de mensagens
        from django.contrib import messages
        messages.error(view.request, str(e))
        return None


def get_servidor(request):
    try:
        return Servidor.objects.get(matricula=request.user.matricula)
    except Servidor.DoesNotExist:
        from django.contrib import messages
        messages.error(request, 'Erro: Servidor não encontrado.')
        raise
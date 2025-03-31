
from dateutil.relativedelta import relativedelta
from django.utils.translation import gettext as _
from .models import Apreensao, Natureza
from datetime import datetime, timedelta
from django.utils.timezone import now






#grafico pizza

def calculate_pie_apreensao():
    # Criar dicionário para armazenar os dados do gráfico
    pie_data = {}

    # Definir o intervalo de 12 meses a partir de agora
    data_inicio = now() - timedelta(days=365)

    # Iterar sobre todas as naturezas disponíveis no modelo Natureza
    naturezas = Natureza.objects.all()

    for natureza in naturezas:
        # Filtrar as apreensões relacionadas à natureza nos últimos 12 meses
        total = natureza.apreensao_set.filter(data__gte=data_inicio).count()

        if total > 0:  # Apenas incluir no gráfico se houver registros
            pie_data[natureza.nome] = total

    # Separar os dados em labels e valores
    labels = list(pie_data.keys())
    values = list(pie_data.values())

    return labels, values




def calculate_bar_chart(queryset, ano_atual, mes_atual):
    """
    Calcula os totais mensais para um queryset filtrado, gerando rótulos e valores para o gráfico de barras.

    :param queryset: Queryset filtrado (ex: Apreensao.objects.all()) sera tudo do model
    :param ano_atual: Ano atual (int)
    :param mes_atual: Mês atual (int)
    :return: Totais mensais (valores) e rótulos dos meses
    """

    monthly_totals = []
    monthly_labels = []

    # Iterar pelos últimos 12 meses
    for i in range(12):
        # Determinar o mês atual da iteração
        current_date = datetime(year=ano_atual, month=mes_atual, day=1) - relativedelta(months=i)
        start_date = current_date.replace(day=1)  # Primeiro dia do mês
        end_date = (current_date + relativedelta(months=1)).replace(day=1)  # Primeiro dia do próximo mês

        # Filtrar registros para o mês atual
        monthly_total = queryset.filter(data__range=(start_date, end_date)).count()

        # Adicionar os totais e os rótulos
        monthly_totals.append(monthly_total)
        month_name = current_date.strftime("%B")
        translated_month_name = _(month_name.capitalize())
        monthly_labels.append(f"{translated_month_name} {current_date.year}")  # Exemplo: "Janeiro 2025"

    # Reverter as listas para ordem cronológica
    monthly_totals.reverse()
    monthly_labels.reverse()

    return monthly_totals, monthly_labels




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



# def add_context_data(context, lista_mes_ajuda, lista_mes_anterior, user, ano_selecionado, mes_selecionado):
#     def calculate_adjusted_total(queryset, carga_horaria):
#         return queryset.filter(carga_horaria=carga_horaria).count()
#
#     ajudas_mes_atual_12h = calculate_adjusted_total(lista_mes_ajuda, '12 horas')
#     ajudas_mes_atual_24h = calculate_adjusted_total(lista_mes_ajuda, '24 horas')
#     ajudas_mes_atual = ajudas_mes_atual_24h + (ajudas_mes_atual_12h / 2)
#
#     ajudas_mes_anterior_12h = calculate_adjusted_total(lista_mes_anterior, '12 horas')
#     ajudas_mes_anterior_24h = calculate_adjusted_total(lista_mes_anterior, '24 horas')
#     ajudas_mes_anterior = ajudas_mes_anterior_24h + (ajudas_mes_anterior_12h / 2)
#
#     variacao_percentual = ((ajudas_mes_atual - ajudas_mes_anterior) / ajudas_mes_anterior) * 100 if ajudas_mes_anterior > 0 else 0
#
#     context.update({
#         'ajudas_mes_atual': round(ajudas_mes_atual),
#         'ajudas_mes_anterior': round(ajudas_mes_anterior),
#         'variacao_percentual': round(variacao_percentual, 2),
#         'bg_class': 'bg-red-600' if variacao_percentual > 0 else 'bg-green-600' if variacao_percentual < 0 else 'bg-gray-600',
#         'servidores_com_ajuda': lista_mes_ajuda.values('matricula').distinct().count(),
#     })
#
#     ajuda_normal_12h = lista_mes_ajuda.filter(majorado=False, carga_horaria='12 horas').count()
#     ajuda_normal_24h = lista_mes_ajuda.filter(majorado=False, carga_horaria='24 horas').count()
#     ajuda_majorado_12h = lista_mes_ajuda.filter(majorado=True, carga_horaria='12 horas').count()
#     ajuda_majorado_24h = lista_mes_ajuda.filter(majorado=True, carga_horaria='24 horas').count()
#
#     ajuda_normal = ajuda_normal_24h + (ajuda_normal_12h / 2)
#     ajuda_majorado = ajuda_majorado_24h + (ajuda_majorado_12h / 2)
#
#     context.update({
#         'pie_values': [round(ajuda_normal, 2), round(ajuda_majorado, 2)],
#         'pie_labels': ['Ajuda Normal', 'Ajuda Majorada'],
#     })
#
#     monthly_totals, monthly_labels = calculate_bar_chart(user, ano_selecionado, mes_selecionado)
#     context.update({
#         'labels_mensais': monthly_labels,
#         'values_mensais': monthly_totals,
#     })









# def build_context(request, context, ano_selecionado, mes_selecionado):
#     user = request.user
#     lista_mes_ajuda, lista_mes_anterior = get_filtered_data(user, mes_selecionado, ano_selecionado)
#     add_context_data(context, lista_mes_ajuda, lista_mes_anterior, user, ano_selecionado, mes_selecionado)
#
#     return context
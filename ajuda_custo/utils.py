# aplicacao/utils.py
from datetime import datetime, timedelta
from .models import LimiteAjudaCusto, Ajuda_Custo, CotaAjudaCusto
from django.contrib import messages
from servidor.models import Servidor
import locale
from django.utils.translation import gettext as _




def get_servidor(request):
    try:
        return Servidor.objects.get(matricula=request.user.matricula)
    except Servidor.DoesNotExist:
        from django.contrib import messages
        messages.error(request, 'Erro: Servidor não encontrado.')
        raise

def get_intervalo_mes(mes, ano):
    inicio_do_mes = datetime(ano, mes, 1)
    fim_do_mes = (inicio_do_mes + timedelta(days=31)).replace(day=1) - timedelta(days=1)
    return inicio_do_mes, fim_do_mes



def get_registros_mes(servidor, inicio_do_mes, fim_do_mes):
    return Ajuda_Custo.objects.filter(matricula=servidor.matricula, data__range=[inicio_do_mes, fim_do_mes])


def calcular_horas_por_unidade(registros_mes):
    horas_por_unidade = {}
    horas_totais = 0
    for registro in registros_mes:
        unidade_nome = registro.unidade
        carga_horaria = int(registro.carga_horaria.strip().replace(' horas', ''))
        horas_totais += carga_horaria
        if unidade_nome not in horas_por_unidade:
            horas_por_unidade[unidade_nome] = carga_horaria
        else:
            horas_por_unidade[unidade_nome] += carga_horaria
    return horas_por_unidade, horas_totais


def get_limites_horas_por_unidade(servidor):
    limites = LimiteAjudaCusto.objects.filter(servidor=servidor)
    limites_horas_por_unidade = {limite.unidade.nome: limite.limite_horas for limite in limites}
    return limites_horas_por_unidade


def calcular_horas_a_adicionar_por_unidade(unidades, cargas_horarias):
    horas_a_adicionar_por_unidade = {}
    for unidade_nome, carga_horaria in zip(unidades, cargas_horarias):
        horas_a_adicionar = int(carga_horaria.strip().replace(' horas', ''))
        if unidade_nome not in horas_a_adicionar_por_unidade:
            horas_a_adicionar_por_unidade[unidade_nome] = horas_a_adicionar
        else:
            horas_a_adicionar_por_unidade[unidade_nome] += horas_a_adicionar
    return horas_a_adicionar_por_unidade


def verificar_limites(horas_totais, horas_a_adicionar_por_unidade, horas_por_unidade, limites_horas_por_unidade, request):
    horas_a_adicionar_total = sum(horas_a_adicionar_por_unidade.values())
    if horas_totais + horas_a_adicionar_total > 192:
        messages.error(request,
                       f'Limite global de 192 horas mensais excedido. Total pretendido: {horas_totais + horas_a_adicionar_total}.')
        return False

    for unidade_nome, horas_a_adicionar in horas_a_adicionar_por_unidade.items():
        horas_atual_unidade = horas_por_unidade.get(unidade_nome, 0)
        limite_unidade = limites_horas_por_unidade.get(unidade_nome, 0)
        if horas_atual_unidade + horas_a_adicionar > limite_unidade:
            messages.error(request,
                           f'Limite de horas para a unidade {unidade_nome} excedido. Limite: {limite_unidade} horas, Total pretendido: {horas_atual_unidade + horas_a_adicionar} horas.')
            return False
    return True


def get_filtered_data(user, mes_selecionado, ano_selecionado):
    unidade_gestor = user.cotaajudacusto_set.first().unidade if user.groups.filter(
        name='Gerente').exists() else None
    previous_month = int(mes_selecionado) - 1 if int(mes_selecionado) > 1 else 12
    previous_year = int(ano_selecionado) if previous_month != 12 else int(ano_selecionado) - 1

    if user.groups.filter(name__in=['Administrador', 'GerGesipe']).exists():
        lista_mes_ajuda = Ajuda_Custo.objects.filter(data__year=ano_selecionado, data__month=mes_selecionado)
        lista_mes_anterior = Ajuda_Custo.objects.filter(data__year=previous_year, data__month=previous_month)

    elif user.groups.filter(name='Gerente').exists():
        lista_mes_ajuda = Ajuda_Custo.objects.filter(
            unidade=unidade_gestor, data__year=ano_selecionado, data__month=mes_selecionado
        )
        lista_mes_anterior = Ajuda_Custo.objects.filter(
            unidade=unidade_gestor, data__year=previous_year, data__month=previous_month
        )

    else:
        lista_mes_ajuda = Ajuda_Custo.objects.filter(matricula=user.matricula)
        lista_mes_anterior = Ajuda_Custo.objects.filter(matricula=user.matricula)

    return lista_mes_ajuda, lista_mes_anterior





def calculate_bar_chart(user, selected_year, selected_month):
    from datetime import datetime
    from dateutil.relativedelta import relativedelta

    unidade_gestor = user.cotaajudacusto_set.first().unidade if user.groups.filter(name='Gerente').exists() else None

    monthly_totals = []
    monthly_labels = []
    for i in range(12):
        date = datetime(year=selected_year, month=selected_month, day=1) - relativedelta(months=i)
        query = Ajuda_Custo.objects.filter(data__year=date.year, data__month=date.month)

        if unidade_gestor:
            query = query.filter(unidade=unidade_gestor)

        ajudas_12h = query.filter(carga_horaria='12 horas').count()
        ajudas_24h = query.filter(carga_horaria='24 horas').count()
        monthly_total = ajudas_24h + (ajudas_12h / 2)
        monthly_totals.append(round(monthly_total, 2))

        month_name = date.strftime("%B")
        translated_month_name = _(month_name.capitalize())
        monthly_labels.append(f"{translated_month_name} {date.year}")  # Adiciona o rótulo no formato "Mês Ano"

    monthly_totals.reverse()
    monthly_labels.reverse()
    return monthly_totals, monthly_labels


def add_context_data(context, lista_mes_ajuda, lista_mes_anterior, user, ano_selecionado, mes_selecionado):
    def calculate_adjusted_total(queryset, carga_horaria):
        return queryset.filter(carga_horaria=carga_horaria).count()

    ajudas_mes_atual_12h = calculate_adjusted_total(lista_mes_ajuda, '12 horas')
    ajudas_mes_atual_24h = calculate_adjusted_total(lista_mes_ajuda, '24 horas')
    ajudas_mes_atual = ajudas_mes_atual_24h + (ajudas_mes_atual_12h / 2)

    ajudas_mes_anterior_12h = calculate_adjusted_total(lista_mes_anterior, '12 horas')
    ajudas_mes_anterior_24h = calculate_adjusted_total(lista_mes_anterior, '24 horas')
    ajudas_mes_anterior = ajudas_mes_anterior_24h + (ajudas_mes_anterior_12h / 2)

    variacao_percentual = ((ajudas_mes_atual - ajudas_mes_anterior) / ajudas_mes_anterior) * 100 if ajudas_mes_anterior > 0 else 0

    context.update({
        'ajudas_mes_atual': round(ajudas_mes_atual),
        'ajudas_mes_anterior': round(ajudas_mes_anterior),
        'variacao_percentual': round(variacao_percentual, 2),
        'bg_class': 'bg-red-600' if variacao_percentual > 0 else 'bg-green-600' if variacao_percentual < 0 else 'bg-gray-600',
        'servidores_com_ajuda': lista_mes_ajuda.values('matricula').distinct().count(),
    })

    ajuda_normal_12h = lista_mes_ajuda.filter(majorado=False, carga_horaria='12 horas').count()
    ajuda_normal_24h = lista_mes_ajuda.filter(majorado=False, carga_horaria='24 horas').count()
    ajuda_majorado_12h = lista_mes_ajuda.filter(majorado=True, carga_horaria='12 horas').count()
    ajuda_majorado_24h = lista_mes_ajuda.filter(majorado=True, carga_horaria='24 horas').count()

    ajuda_normal = ajuda_normal_24h + (ajuda_normal_12h / 2)
    ajuda_majorado = ajuda_majorado_24h + (ajuda_majorado_12h / 2)

    context.update({
        'pie_values': [round(ajuda_normal, 2), round(ajuda_majorado, 2)],
        'pie_labels': ['Ajuda Normal', 'Ajuda Majorada'],
    })

    monthly_totals, monthly_labels = calculate_bar_chart(user, ano_selecionado, mes_selecionado)
    context.update({
        'labels_mensais': monthly_labels,
        'values_mensais': monthly_totals,
    })

    if user.groups.filter(name='Gerente').exists():
        try:
            cota = CotaAjudaCusto.objects.get(gestor=user)
            context['unidade_gerente'] = cota.unidade.nome
        except CotaAjudaCusto.DoesNotExist:
            context['unidade_gerente'] = "Unidade não encontrada"
    else:
        context['unidade_gerente'] = None





def build_context(request, context, ano_selecionado, mes_selecionado):
    user = request.user
    lista_mes_ajuda, lista_mes_anterior = get_filtered_data(user, mes_selecionado, ano_selecionado)
    add_context_data(context, lista_mes_ajuda, lista_mes_anterior, user, ano_selecionado, mes_selecionado)

    return context

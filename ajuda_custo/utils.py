# aplicacao/utils.py
from datetime import datetime, timedelta
from .models import LimiteAjudaCusto, Ajuda_Custo, CotaAjudaCusto
from django.contrib import messages
from servidor.models import Servidor
import locale
from django.utils.translation import gettext as _
import uuid
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta
from django.utils.timezone import now
from django.utils import timezone
from datetime import datetime
from dateutil.relativedelta import relativedelta


def gerar_e_armazenar_codigo(request):
    codigo = str(uuid.uuid4())[:6]
    expiracao = timezone.now() + timezone.timedelta(minutes=5)  # Agora com timezone
    print(f'codigo de verificacao {codigo} expira em {expiracao.isoformat()}')

    # Armazenar como string ISO
    request.session['codigo_verificacao'] = codigo
    request.session['codigo_verificacao_expira'] = expiracao.isoformat()

    enviar_email_verificacao(request.user.email, codigo)
    return codigo, expiracao


def enviar_email_verificacao(email, codigo):
    assunto = 'Seu código de verificação'
    mensagem_html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 0;">
            <div style="background-color: #f7f7f7; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
                    <div style="padding: 20px; text-align: center; background-color: #4CAF50; color: white; font-size: 24px;">
                        Código de Verificação
                    </div>
                    <div style="padding: 20px;">
                        <p style="font-size: 16px; line-height: 1.5; color: #333;">
                            Olá,
                        </p>
                        <p style="font-size: 16px; line-height: 1.5; color: #333; text-align: center">
                            Seu código de verificação é: <strong style="font-size: 22px;">{codigo}</strong>
                        </p>
                        <p style="font-size: 14px; color: #555; margin-top: 20px;">
                            Este código é válido por 5 minutos. Caso você não tenha solicitado este código, por favor, ignore esta mensagem.
                        </p>
                    </div>
                    <div style="padding: 20px; text-align: center; background-color: #f7f7f7; color: #888; font-size: 12px;">
                        © {2025} SEAP. Todos os direitos reservados.
                    </div>
                </div>
            </div>
        </body>
    </html>
    """

    send_mail(
        subject=assunto,
        message='',  # Deixe vazio, já que estamos usando HTML
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        html_message=mensagem_html,  # Adiciona o conteúdo em HTML
    )


def verificar_codigo_expiracao(expira_em):
    if not expira_em:
        return False

    # Converter a string ISO para datetime com timezone
    expiracao = timezone.datetime.fromisoformat(expira_em)
    # Comparar dois datetimes com timezone
    return timezone.now() < expiracao


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


#funcoes graficos
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
        lista_mes_ajuda = Ajuda_Custo.objects.filter(
            matricula=user.matricula, data__year=ano_selecionado, data__month=mes_selecionado
        )
        lista_mes_anterior = Ajuda_Custo.objects.filter(
            matricula=user.matricula, data__year=previous_year, data__month=previous_month
        )

    return lista_mes_ajuda, lista_mes_anterior


def calculate_bar_chart(user, selected_year, selected_month):
    # Verifica se o usuário é um gerente e obtém a unidade gerenciada
    unidade_gestor = user.cotaajudacusto_set.first().unidade if user.groups.filter(name='Gerente').exists() else None

    monthly_totals = []
    monthly_labels = []

    for i in range(12):
        # Calcula a data para o mês atual da iteração
        date = datetime(year=selected_year, month=selected_month, day=1) - relativedelta(months=i)

        # Filtra os dados com base no tipo de usuário
        if user.groups.filter(name__in=['Administrador', 'GerGesipe']).exists():
            # Administrador ou GerGesipe: todos os dados
            query = Ajuda_Custo.objects.filter(data__year=date.year, data__month=date.month)
        elif user.groups.filter(name='Gerente').exists():
            # Gerente: apenas os dados da unidade gerenciada
            query = Ajuda_Custo.objects.filter(unidade=unidade_gestor, data__year=date.year, data__month=date.month)
        else:
            # Outros usuários: apenas os dados relacionados ao próprio usuário
            query = Ajuda_Custo.objects.filter(matricula=user.matricula, data__year=date.year, data__month=date.month)

        # Calcula o total de ajudas de custo para o mês
        ajudas_12h = query.filter(carga_horaria='12 horas').count()
        ajudas_24h = query.filter(carga_horaria='24 horas').count()
        monthly_total = ajudas_24h + (ajudas_12h / 2)
        monthly_totals.append(round(monthly_total, 2))

        # Adiciona o rótulo no formato "Mês Ano"
        month_name = date.strftime("%B")
        translated_month_name = _(month_name.capitalize())
        monthly_labels.append(f"{translated_month_name} {date.year}")

    # Inverte as listas para exibir do mais antigo para o mais recente
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


def datas_adicionar(dias, unidades, cargas_horarias, servidor, nome_servidor, mes, ano, request):
    error_messages = []
    ajuda_custo_instances = []


    for dia, unidade_nome, carga_horaria in zip(dias, unidades, cargas_horarias):
        try:
            data_completa = datetime.strptime(f"{dia}/{mes}/{ano}", "%d/%m/%Y").date()
            print(f"Processando data: {data_completa}")
            horas_a_adicionar = int(carga_horaria.strip().replace(' horas', ''))


            carga_horaria_final = f"{horas_a_adicionar} horas"
            ajuda_custo = Ajuda_Custo(
                matricula=servidor.matricula,
                nome=nome_servidor,
                data=data_completa,
                unidade=unidade_nome.strip(),
                carga_horaria=carga_horaria_final
            )

            ajuda_custo_instances.append(ajuda_custo)
            print(f"informacao adicionada: {ajuda_custo}")

        except Exception as e:
            print(f"Erro ao processar data {dia.strip()}/{mes}/{ano}: {e}")
            error_messages.append(f'Ocorreu um erro ao processar a data {dia.strip()}/{mes}/{ano}.')

    return ajuda_custo_instances, error_messages


def build_context(request, context, ano_selecionado, mes_selecionado):
    user = request.user
    lista_mes_ajuda, lista_mes_anterior = get_filtered_data(user, mes_selecionado, ano_selecionado)
    add_context_data(context, lista_mes_ajuda, lista_mes_anterior, user, ano_selecionado, mes_selecionado)

    return context

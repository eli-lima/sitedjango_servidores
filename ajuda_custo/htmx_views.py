from .models import Ajuda_Custo
from django.db.models import Q
from django.shortcuts import render
from django.utils.dateparse import parse_date
from django.db.models import OuterRef, Subquery


def ajuda_custo_list(request):
    user = request.user
    query = request.GET.get('query', '')
    data_inicial = request.GET.get('dataInicial')
    data_final = request.GET.get('dataFinal')

    # Converte as datas em objetos datetime, se fornecidas
    data_inicial = parse_date(data_inicial) if data_inicial else None
    data_final = parse_date(data_final) if data_final else None

    # Verificação dos grupos de usuário
    if user.groups.filter(name__in=['Administrador', 'GerGesipe']).exists():
        # Acesso completo para Administradores e GerGesipe
        queryset = Ajuda_Custo.objects.all()
    elif user.groups.filter(name='Gerente').exists():
        # Acesso limitado à unidade do gestor
        try:
            unidade_gestor = user.cotaajudacusto_set.first().unidade
            queryset = Ajuda_Custo.objects.filter(unidade=unidade_gestor)
        except AttributeError:
            # Caso o gestor não tenha uma unidade atribuída
            queryset = Ajuda_Custo.objects.none()
    else:
        # Acesso limitado ao próprio usuário
        queryset = Ajuda_Custo.objects.filter(matricula=user.matricula)

    # Aplica os filtros de data se fornecidos
    if data_inicial and data_final:
        queryset = queryset.filter(data__range=[data_inicial, data_final])
    elif data_inicial:
        queryset = queryset.filter(data__gte=data_inicial)
    elif data_final:
        queryset = queryset.filter(data__lte=data_final)

    # Filtra pela query de pesquisa
    if query:
        queryset = queryset.filter(Q(nome__icontains=query) | Q(matricula__icontains=query))

    # Obtém as 50 datas mais recentes após aplicar todos os filtros
    queryset = queryset.order_by('-data')[:50]


    context = {
        'datas': queryset,
        'query': query,
        'dataInicial': data_inicial,
        'dataFinal': data_final,
    }

    return render(request, 'partials/ajuda_custo_partial.html', context)


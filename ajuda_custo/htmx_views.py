from django.http import HttpResponse
from .models import Ajuda_Custo
from django.db.models import Q
from django.shortcuts import render
from django.utils.dateparse import parse_date
from datetime import datetime, timedelta


def ajuda_custo_list(request):
    user = request.user
    query = request.GET.get('query', '')
    data_inicial = request.GET.get('dataInicial')
    data_final = request.GET.get('dataFinal')

    # Converte as datas em objetos datetime, se fornecidas
    data_inicial = parse_date(data_inicial) if data_inicial else None
    data_final = parse_date(data_final) if data_final else None



    # Filtro básico com base na query de pesquisa
    if user.groups.filter(name__in=['Administrador', 'GerGesipe']).exists():
        queryset = Ajuda_Custo.objects.all()
    else:
        queryset = Ajuda_Custo.objects.filter(matricula=user.matricula)

    # Filtro de busca por nome ou matrícula
    if query:
        queryset = queryset.filter(
            Q(nome__icontains=query) | Q(matricula__icontains=query)
        )

    # Aplica os filtros de data se fornecidos
    if data_inicial and data_final:
        queryset = queryset.filter(data__range=[data_inicial, data_final])
    elif data_inicial:
        queryset = queryset.filter(data__gte=data_inicial)
    elif data_final:
        queryset = queryset.filter(data__lte=data_final)

    context = {
        'datas': queryset.order_by('nome'),
        'query': query,
        'dataInicial': data_inicial,
        'dataFinal': data_final,
    }
    print(data_inicial, '---------', data_final)
    return render(request, 'partials/ajuda_custo_partial.html', context)
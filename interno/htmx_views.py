from .models import Interno
from django.db.models import Q
from django.shortcuts import render


def interno_list(request):
    prontuario = request.GET.get('prontuario', '')
    cpf = request.GET.get('cpf', '')
    nome_mae = request.GET.get('nome_mae', '')
    query = request.GET.get('query', '')

    # Filtro inicial
    queryset = Interno.objects.all()

    # Aplicar filtros específicos
    if prontuario:
        queryset = queryset.filter(prontuario__icontains=prontuario)
    if cpf:
        queryset = queryset.filter(cpf__icontains=cpf)
    if nome_mae:
        queryset = queryset.filter(nome_mae__icontains=nome_mae)
    if query:
        queryset = queryset.filter(
            Q(prontuario__icontains=query) |
            Q(nome__icontains=query) |
            Q(cpf__icontains=query) |
            Q(nome_mae__icontains=query)
        )

    # Ordenar e limitar resultados
    queryset = queryset.order_by('-prontuario')[:50]

    return render(request, 'partials/interno_partial.html', {
        'datas': queryset
    })


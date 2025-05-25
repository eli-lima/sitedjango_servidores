from .models import Armamento
from django.db.models import Q
from django.shortcuts import render


def armamento_list(request):
    unidade = request.GET.get('unidade_arm', '')
    modelo = request.GET.get('modelo', '')
    numero_serie = request.GET.get('numero_serie', '')
    query = request.GET.get('query', '')

    queryset = Armamento.objects.all()

    if unidade:
        queryset = queryset.filter(unidade__nome__icontains=unidade)
    if modelo:
        queryset = queryset.filter(modelo__nome__icontains=modelo)
    if numero_serie:
        queryset = queryset.filter(numero_serie__icontains=numero_serie)
    if query:
        queryset = queryset.filter(
            Q(modelo__nome__icontains=query) |
            Q(tipo_arma__nome__icontains=query) |
            Q(numero_serie__icontains=query) |
            Q(servidor__nome__icontains=query) |
            Q(unidade__nome__icontains=query)
        )

    queryset = queryset.order_by('modelo__nome')[:50]

    return render(request, 'partials/armamento_list.html', {
        'armamentos': queryset
    })


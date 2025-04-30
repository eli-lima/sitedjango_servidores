

from django.shortcuts import render
from servidor.models import Servidor
from django.http import HttpResponse


def buscar_servidor(request):
    matricula = request.GET.get('matricula', '').strip()

    if not matricula:
        return HttpResponse("")

    try:
        servidor = Servidor.objects.get(matricula=matricula)
        return render(request, 'partials/dados_servidor.html', {
            'servidor': servidor
        })
    except Servidor.DoesNotExist:
        return HttpResponse("""
            <div class="text-red-500 p-2">
                Servidor não encontrado. Verifique a matrícula.
            </div>
        """)



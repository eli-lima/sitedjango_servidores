from .models import Gesipe_adm


def lista_edicoes_recentes(request):
    lista_ultimas_edicoes = Gesipe_adm.objects.all().order_by('-data_edicao')[0:10]

    return {"lista_edicoes_recentes": lista_ultimas_edicoes}


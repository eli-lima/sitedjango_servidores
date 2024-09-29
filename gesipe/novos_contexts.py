from .models import Gesipe_adm


def lista_edicoes_recentes(request):
    lista_ultimas_edicoes = Gesipe_adm.objects.all().order_by('-data_edicao')[0:10]

    return {"lista_edicoes_recentes": lista_ultimas_edicoes}




# from ajuda_custo.models import DataMajorada  # Importe o modelo correto
# from datetime import datetime
#
# # Lista de datas no formato dd/mm/yyyy
# datas = [
#     "01/01/2029", "05/01/2029", "06/01/2029", "07/01/2029",
#     "12/01/2029", "13/01/2029", "14/01/2029", "19/01/2029",
#
#
# ]
#
#
# for data_str in datas:
#     data_formatada = datetime.strptime(data_str, "%d/%m/%Y").date()
#     DataMajorada.objects.get_or_create(data=data_formatada)
#     print(f"Data {data_str} inserida com sucesso.")
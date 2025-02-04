from .models import Unidade


def get_unidade_choices():
    # Mova a lógica de consulta para uma função separada
    return [('', '--- Selecione uma unidade ---')] + [(u.nome, u.nome) for u in Unidade.objects.all().order_by('nome')]


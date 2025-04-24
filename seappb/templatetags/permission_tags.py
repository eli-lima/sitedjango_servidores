# permission_tags.py
from django import template
from django.contrib.auth.models import Group
from seappb.models import PermissaoSecao  # Substitua 'sua_app' pelo nome do seu app
from django.core.cache import cache

register = template.Library()



@register.filter(name='permitido')
def verificar_permissao(user, nome_secao, usar_cache=True):
    """
    Verifica se o usuário tem permissão para ver uma seção específica
    Parâmetros:
        user: usuário logado
        nome_secao: string identificando a seção (ex: 'graficos')
        usar_cache: define se deve usar cache (opcional, padrão True)
    """
    if user.is_superuser:
        return True

    if usar_cache:
        cache_key = f'permissao_{user.id}_{nome_secao}'
        resultado_cache = cache.get(cache_key)

        if resultado_cache is not None:
            return resultado_cache

    # Consulta ao banco de dados
    tem_permissao = PermissaoSecao.objects.filter(
        nome_secao=nome_secao,
        grupo__in=user.groups.all()
    ).exists()

    if usar_cache:
        cache.set(cache_key, tem_permissao, timeout=300)  # 5 minutos

    return tem_permissao

from django.contrib.auth.models import Group
from django.core.cache import cache
from seappb.models import PermissaoSecao  # Ajuste o import conforme necessário


class PermissionChecker:
    @classmethod
    def has_permission(cls, user, permission_section, use_cache=True):
        """
        Verifica se o usuário tem permissão para uma seção específica

        Args:
            user: usuário autenticado
            permission_section: string identificando a seção (ex: 'edit_populacao')
            use_cache: define se deve usar cache (padrão True)
        """
        if user.is_superuser:
            return True

        if use_cache:
            cache_key = f'permission_{user.id}_{permission_section}'
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

        try:
            section = PermissaoSecao.objects.get(nome_secao=permission_section)
            has_perm = user.groups.filter(id__in=section.grupos.all()).exists()
        except PermissaoSecao.DoesNotExist:
            has_perm = False

        if use_cache:
            cache.set(cache_key, has_perm, timeout=300)

        return has_perm

    @classmethod
    def get_permitted_groups(cls, permission_section):
        """
        Retorna os grupos que têm permissão para uma seção específica
        """
        try:
            section = PermissaoSecao.objects.get(nome_secao=permission_section)
            return section.grupos.all()
        except PermissaoSecao.DoesNotExist:
            return Group.objects.none()
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Setor, Unidade, PermissaoSecao
from servidor.models import Servidor

# Registrar Setor com customizações
class SetorAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome')


admin.site.register(Setor, SetorAdmin)


@admin.register(Unidade)
class UnidadeAdmin(admin.ModelAdmin):
    # Definir quais campos aparecerão na listagem de Ajuda_Custo
    list_display = ('nome', 'cidade', 'reisp')
    #
    # Definir os campos que podem ser pesquisados (campo de pesquisa no topo da lista)
    search_fields = ('nome', 'reisp', 'cidade')
    #
    # Adicionar filtros laterais
    list_filter = ('reisp', 'nome')

    # Habilitar a ordenação por nome
    ordering = ('nome',)

# Registrar Usuario com customizações


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    autocomplete_fields = ['servidor']  # Usa autocomplete para selecionar o servidor
    search_fields = ['username', 'nome_completo', 'email', 'matricula']  # Permite busca

    list_display = ('username', 'nome_completo', 'email', 'setor', 'is_staff', 'servidor')  # Listagem principal

    fieldsets = (
        (None, {
            'fields': ('username', 'password', 'nome_completo', 'email', 'foto_perfil', 'matricula', 'servidor', 'setor')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )

# Também precisa registrar o modelo de Servidor para funcionar o autocomplete
@admin.register(Servidor)
class ServidorAdmin(admin.ModelAdmin):
    search_fields = ['nome', 'matricula']


@admin.register(PermissaoSecao)
class PermissaoSecaoAdmin(admin.ModelAdmin):
    list_display = ('nome_secao', 'listar_grupos', 'descricao')
    list_filter = ('grupos',)
    search_fields = ('nome_secao', 'descricao')

    def listar_grupos(self, obj):
        return ", ".join([g.name for g in obj.grupos.all()])
    listar_grupos.short_description = 'Grupos'

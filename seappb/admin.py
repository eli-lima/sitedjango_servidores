from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Setor, Unidade, PermissaoSecao

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
class UsuarioAdmin(UserAdmin):
    # Customizar os campos exibidos no formulário de admin
    fieldsets = (
        (None, {'fields': ('username', 'password', 'nome_completo', 'email', 'foto_perfil', 'matricula', 'setor')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Listagem personalizada no admin
    list_display = ('username', 'nome_completo', 'email', 'setor', 'is_staff')

admin.site.register(Usuario, UsuarioAdmin)

@admin.register(PermissaoSecao)
class PermissaoSecaoAdmin(admin.ModelAdmin):
    list_display = ('nome_secao', 'grupo', 'descricao')
    list_filter = ('grupo',)
    search_fields = ('nome_secao', 'descricao')
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Setor

# Registrar Setor com customizações
class SetorAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome')

admin.site.register(Setor, SetorAdmin)
# admin.site.register(Unidade)

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

from django.contrib import admin
from .models import Usuario
from django.contrib.auth.admin import UserAdmin

# só existe porque a gente quer que no admin apareça o campo personalizado filmes_vistos
campos = list(UserAdmin.fieldsets)
campos.append(
    ("Informações Funcionais", {'fields': ('matricula', 'setor', 'foto_perfil')})
)
UserAdmin.fieldsets = tuple(campos)

# Register your models here.

admin.site.register(Usuario, UserAdmin)



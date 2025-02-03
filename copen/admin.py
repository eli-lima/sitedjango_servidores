from django.contrib import admin
from .models import (Ocorrencia, Apreensao, TipoOcorrencia,
                     Atendimento, Mp, TipoMp, Objeto,
                     Natureza)

# Register your models here.

admin.site.register(Ocorrencia)
admin.site.register(Apreensao)

admin.site.register(TipoOcorrencia)
admin.site.register(Atendimento)
admin.site.register(TipoMp)
admin.site.register(Mp)
admin.site.register(Objeto)
admin.site.register(Natureza)
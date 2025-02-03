from django.contrib import admin
from .models import (Ocorrencia, Apreensao, TipoOcorrencia,
                     Atendimento, Mp, TipoMp)

# Register your models here.

admin.site.register(Ocorrencia)
admin.site.register(Apreensao)

admin.site.register(TipoOcorrencia)
admin.site.register(Atendimento)
admin.site.register(TipoMp)
admin.site.register(Mp)
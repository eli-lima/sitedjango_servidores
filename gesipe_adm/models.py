from django.db import models
from datetime import datetime
from django.utils import timezone


# Create your models here.
class Gesipe_adm(models.Model):
    data = models.DateField(default=timezone.now)
    processos = models.IntegerField(default=0)
    memorandos_diarias = models.IntegerField(default=0)
    memorandos_documentos_capturados = models.IntegerField(default=0)
    despachos_gerencias = models.IntegerField(default=0)
    despachos_unidades = models.IntegerField(default=0)
    despachos_grupos = models.IntegerField(default=0)
    oficios_internos_unidades_prisionais = models.IntegerField(default=0)
    oficios_internos_setores_seap_pb = models.IntegerField(default=0)
    oficios_internos_circular = models.IntegerField(default=0)
    oficios_externos_seap_pb = models.IntegerField(default=0)
    oficios_externos_diversos = models.IntegerField(default=0)
    oficios_externos_judiciario =models.IntegerField(default=0)
    os_grupos = models.IntegerField(default=0)
    os_diversos = models.IntegerField(default=0)
    portarias = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    data_edicao = models.DateTimeField(default=timezone.now)
    usuario_id = models.IntegerField()

    def __str__(self):
        return self.data.strftime("%d/%m/%Y")
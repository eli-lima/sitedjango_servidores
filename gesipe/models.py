from django.db import models
from datetime import datetime
from django.utils import timezone


# Create your models here.
class Gesipe_adm(models.Model):
    data = models.DateField(default=timezone.now, unique=True)
    processos = models.IntegerField(default=0, blank=True)
    diarias = models.IntegerField(default=0, blank=True)
    documentos_capturados = models.IntegerField(default=0, blank=True)
    despachos_gerencias = models.IntegerField(default=0, blank=True)
    despachos_unidades = models.IntegerField(default=0, blank=True)
    despachos_grupos = models.IntegerField(default=0, blank=True)
    oficios_internos_unidades_prisionais = models.IntegerField(default=0, blank=True)
    oficios_internos_setores_seap_pb = models.IntegerField(default=0, blank=True)
    oficios_internos_circular = models.IntegerField(default=0, blank=True)
    oficios_externos_seap_pb = models.IntegerField(default=0, blank=True)
    oficios_externos_diversos = models.IntegerField(default=0, blank=True)
    oficios_externos_judiciario = models.IntegerField(default=0, blank=True)
    os_grupos = models.IntegerField(default=0, blank=True)
    os_diversos = models.IntegerField(default=0, blank=True)
    portarias = models.IntegerField(default=0, blank=True)
    total_memorando = models.IntegerField(default=0, blank=True)
    total_despacho = models.IntegerField(default=0, blank=True)
    total_oficio = models.IntegerField(default=0, blank=True)
    total_os = models.IntegerField(default=0, blank=True)
    total = models.IntegerField(default=0, blank=True)
    data_edicao = models.DateTimeField(default=timezone.now)
    usuario = models.ForeignKey('seappb.Usuario', on_delete=models.CASCADE, related_name='edicoes_adm')

    def save(self, *args, **kwargs):
        self.total = (self.processos + self.diarias +
                      self.documentos_capturados + self.despachos_gerencias +
                      self.despachos_unidades + self.despachos_grupos +
                      self.oficios_internos_unidades_prisionais + self.oficios_internos_setores_seap_pb +
                      self.oficios_internos_circular + self.oficios_externos_seap_pb +
                      self.oficios_externos_diversos + self.oficios_externos_judiciario +
                      self.os_grupos + self.os_diversos + self.portarias)
        self.total_despacho = (self.despachos_gerencias + self.despachos_unidades + self.despachos_grupos)
        self.total_oficio = (self.oficios_internos_circular + self.oficios_internos_unidades_prisionais +
                             self.oficios_internos_setores_seap_pb + self.oficios_externos_seap_pb +
                             self.oficios_externos_judiciario + self.oficios_externos_diversos)
        self.total_os = (self.os_grupos + self.os_diversos)
        super(Gesipe_adm, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.usuario} - {self.data.strftime('%d/%m/%Y')}"

class Gesipe_Sga(models.Model):
    data = models.DateField(default=timezone.now)
    agendamentos_entradas = models.IntegerField(default=0, blank=True)
    comunicacoes_presos = models.IntegerField(default=0, blank=True)
    comunicacoes_servidores = models.IntegerField(default=0, blank=True)
    comunicacoes_setores = models.IntegerField(default=0, blank=True)
    comunicacoes_judiciais_externas = models.IntegerField(default=0, blank=True)
    om_grupos = models.IntegerField(default=0, blank=True)
    om_unidades = models.IntegerField(default=0, blank=True)
    data_edicao = models.DateTimeField(default=timezone.now)
    usuario = models.ForeignKey('seappb.Usuario', on_delete=models.CASCADE, related_name='edicoes_sga')

    class Meta:
        indexes = [
            models.Index(fields=['data']),
        ]

    def __str__(self):
        return f"{self.usuario} - {self.data.strftime('%d/%m/%Y')}"
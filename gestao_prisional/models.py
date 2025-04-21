from django.db import models
from servidor.models import Servidor
from seappb.models import Unidade, Usuario
from django.utils import timezone
# # Create your models here.


class OcorrenciaPlantao(models.Model):
    data = models.DateField(default=timezone.now)
    chefe_equipe = models.ForeignKey('servidor.Servidor', on_delete=models.CASCADE)
    descricao = models.TextField()
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE, null=True, blank=True)
    servidores_ordinario = models.ManyToManyField(Servidor, related_name='plantoes_ordinarios')
    servidores_extraordinario = models.ManyToManyField(Servidor, related_name='plantoes_extraordinarios')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    observacao = models.TextField(null=True, blank=True)
    data_edicao = models.DateTimeField(default=timezone.now)
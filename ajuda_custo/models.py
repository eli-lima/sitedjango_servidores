from django.db import models
from django.utils import timezone
import os
from datetime import datetime
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


# Create your models here.


def upload_to_ajuda_custo(instance, filename):
    # Cria a pasta no formato "ajuda_custo/ano-mes/matricula/arquivo"
    data_formatada = instance.data.strftime('%Y-%m')  # Formato "ano-mes"
    pasta_matricula = f'{instance.matricula}/'

    # Adiciona a pasta raiz 'ajuda_custo' antes do resto do caminho
    caminho_completo = f'ajuda_custo/{data_formatada}/{pasta_matricula}{filename}'

    # Adiciona um print para verificar o caminho gerado
    print(f"Path gerado para upload: {caminho_completo}")

    return caminho_completo


class DataMajorada(models.Model):
    data = models.DateField(unique=True)

    def __str__(self):
        return self.data.strftime("%d/%m/%Y")


#cadastrar unidades





CARGA_HORARIA = [
        ('12 horas', '12 Horas'),
        ('24 horas', '24 Horas'),
    ]


class Ajuda_Custo(models.Model):
    matricula = models.IntegerField()  # Armazena o valor da matrícula diretamente
    nome = models.CharField(max_length=100)
    data = models.DateField()
    unidade = models.CharField(max_length=100)  # Armazena o nome da unidade diretamente
    carga_horaria = models.CharField(max_length=30, choices=CARGA_HORARIA)  # 12 OU 21
    data_edicao = models.DateTimeField(default=timezone.now)
    majorado = models.BooleanField(default=False)





    def __str__(self):
        return f"{self.nome} - {self.data.strftime('%d/%m/%Y')}"


# Sinal para atualizar o campo `majorado` quando uma nova data majorada é adicionada
@receiver(post_save, sender=DataMajorada)
def atualizar_majorado_ao_adicionar(sender, instance, **kwargs):
    # Atualiza todos os registros de Ajuda_Custo com a data majorada
    Ajuda_Custo.objects.filter(data=instance.data).update(majorado=True)


# Sinal para atualizar o campo `majorado` quando uma data majorada é removida
@receiver(post_delete, sender=DataMajorada)
def atualizar_majorado_ao_remover(sender, instance, **kwargs):
    # Atualiza todos os registros de Ajuda_Custo com a data removida, definindo `majorado` como False
    Ajuda_Custo.objects.filter(data=instance.data).update(majorado=False)


class LimiteAjudaCusto(models.Model):
    servidor = models.ForeignKey('servidor.Servidor', on_delete=models.CASCADE)
    limite_horas = models.IntegerField()  # Limite de horas mensais para o servidor

    def __str__(self):
        return f"{self.servidor.nome} - {self.limite_horas} horas/mês"


from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from seappb.models import Unidade

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
    folha_assinada = models.FileField(upload_to=upload_to_ajuda_custo, blank=True,
                                          null=True)  # Campo de upload com pasta dinâmica
    codigo_verificacao = models.CharField(max_length=6, blank=True, null=True)  # Novo campo

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
    unidade = models.ForeignKey('seappb.Unidade', default=1, on_delete=models.CASCADE)  # Adiciona a unidade
    limite_horas = models.IntegerField()  # Limite de horas mensais para o servidor

    def __str__(self):
        return f"{self.servidor.nome} - {self.limite_horas} horas/mês"


class CotaAjudaCusto(models.Model):
    gestor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE)
    cota_ajudacusto = models.PositiveIntegerField()  # Em dias
    carga_horaria_total = models.PositiveIntegerField(editable=False, default=0)  # Em horas
    carga_horaria_disponivel = models.PositiveIntegerField(editable=False, default=0)

    def save(self, *args, **kwargs):
        # Certifica-se de que somente um gerente por unidade por vez
        existing_cota = CotaAjudaCusto.objects.filter(unidade=self.unidade).exclude(pk=self.pk).first()
        if existing_cota:
            existing_cota.delete()

        # Converte a cota mensal para horas
        self.carga_horaria_total = self.cota_ajudacusto * 24

        # Recalcula as horas distribuídas
        distribuidas = LimiteAjudaCusto.objects.filter(unidade=self.unidade).aggregate(
            total_distribuido=Sum('limite_horas')
        )['total_distribuido'] or 0

        # Atualiza a carga horária disponível
        self.carga_horaria_disponivel = self.carga_horaria_total - distribuidas

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.gestor} - {self.unidade} - Cota: {self.cota_ajudacusto} dias ({self.carga_horaria_total} horas)"

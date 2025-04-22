from django.db import models
from seappb.models import Unidade, Usuario
from gestao_prisional.models import OcorrenciaPlantao
from datetime import datetime
from django.utils.deconstruct import deconstructible
import os


@deconstructible
class PathAndRename:
    def __init__(self, sub_folder):
        self.sub_folder = sub_folder

    def __call__(self, instance, filename):
        # Usa o ID e nome do interno para criar uma pasta única
        id_nome = f"{instance.id}_{instance.nome}"
        # Garante que o nome do arquivo seja seguro
        filename = os.path.basename(filename)
        # Gera o caminho completo onde a imagem será salva
        return os.path.join(self.sub_folder, id_nome, filename)


# Instancia a função de caminho de upload
upload_to = PathAndRename('internos_fotos')


class Interno(models.Model):
    prontuario = models.IntegerField(unique=True)
    nome = models.CharField(max_length=255, db_index=True)
    cpf = models.CharField(max_length=100, blank=True, null=True)
    nome_mae = models.CharField(max_length=255, blank=True, null=True)
    unidade = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    data_extracao = models.DateField()
    codificacao_facial = models.TextField(blank=True, null=True)  # Armazena a codificação facial como JSON
    foto = models.ImageField(upload_to=upload_to, blank=True, null=True)  # Usando a função de upload personalizada

    def __str__(self):
        return f"{self.nome} (Prontuário: {self.prontuario})"


class PopulacaoCarceraria(models.Model):
    plantao = models.ForeignKey('gestao_prisional.OcorrenciaPlantao', on_delete=models.CASCADE, related_name='populacoes', null=True, blank=True)
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE, related_name='populacao_carceraria')
    data_atualizacao = models.DateField(default=datetime.now)  # Data da última atualização

    # Quantidades por regime
    regime_aberto = models.IntegerField(default=0)
    regime_semiaberto = models.IntegerField(default=0)
    regime_fechado = models.IntegerField(default=0)
    regime_domiciliar = models.IntegerField(default=0)

    # Quantidades por status
    provisorio = models.IntegerField(default=0)
    sentenciado = models.IntegerField(default=0)

    # Quantidades por gênero
    masculino = models.IntegerField(default=0)
    feminino = models.IntegerField(default=0)
    outros = models.IntegerField(default=0)


    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)

    # Total de presos (pode ser calculado ou preenchido manualmente)
    total = models.IntegerField(default=0)

    def __str__(self):
        return f"População Carcerária - {self.unidade.nome} ({self.data_atualizacao})"

    def save(self, *args, **kwargs):
        # Calcula o total automaticamente ao salvar
        self.total = (
            self.regime_aberto + self.regime_semiaberto + self.regime_fechado + self.regime_domiciliar
        )
        super().save(*args, **kwargs)



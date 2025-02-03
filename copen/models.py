from django.db import models
from django.utils import timezone
from seappb.models import Usuario, Unidade
from interno.models import Interno
from servidor.models import Servidor

# Create your models here.

#models atendimentos

class Atendimento(models.Model):
    data = models.DateField(default=timezone.now)
    nome = models.CharField(max_length=255)
    prontuario = models.CharField(max_length=255, null=True, blank=True)
    localizado = models.BooleanField(default=False)
    servidor = models.ForeignKey(Servidor, on_delete=models.CASCADE, null=True, blank=True)
    outros = models.CharField(max_length=100, null=True, blank=True)
    matricula = models.CharField(max_length=20, null=True, blank=True)
    instituicao = models.CharField(max_length=100, null=True, blank=True)
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE, null=True, blank=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    observacao = models.TextField(null=True, blank=True)
    data_edicao = models.DateTimeField(default=timezone.now)


    def __str__(self):
        return f"{self.data} - {self.data.strftime('%d/%m/%Y')}"





#models ocorrencias








# models apreensoes
class Natureza(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


class Objeto(models.Model):
    nome = models.CharField(max_length=100)
    natureza = models.ForeignKey(Natureza, on_delete=models.CASCADE, related_name='objetos')

    def __str__(self):
        return self.nome

class Apreensao(models.Model):
    data = models.DateField(default=timezone.now)
    natureza = models.ForeignKey(Natureza, on_delete=models.CASCADE)
    objeto = models.ForeignKey(Objeto, on_delete=models.CASCADE)
    quantidade = models.IntegerField(default=0)  # Alterado para IntegerField
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE)
    descricao = models.TextField()
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    observacao = models.TextField(null=True, blank=True)
    data_edicao = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.natureza} - {self.data.strftime('%d/%m/%Y')}"


#tabelas custodias


class Custodia(models.Model):
    interno = models.ForeignKey(Interno, on_delete=models.CASCADE)
    unidade_hospitalar = models.CharField(max_length=100)
    unidade_solicitante = models.ForeignKey(Unidade, on_delete=models.CASCADE)
    responsavel = models.CharField(max_length=100)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    observacao = models.TextField(null=True, blank=True)
    data_entrada = models.DateField(default=timezone.now)
    data_saida = models.DateField(default=timezone.now, null=True, blank=True)
    data_edicao = models.DateTimeField(default=timezone.now)


    def __str__(self):
        data_saida_str = self.data_saida.strftime('%d/%m/%Y') if self.data_saida else 'Ainda vigente'
        return f"{self.interno} - {self.data_entrada.strftime('%d/%m/%Y')} - {data_saida_str}"



# mandados de prisao

class TipoMp(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


class Mp(models.Model):
    tipo = models.ForeignKey(TipoMp, on_delete=models.CASCADE)
    interno = models.ForeignKey(Interno, on_delete=models.CASCADE)
    nome_mae = models.CharField(max_length=100)
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    observacao = models.TextField(null=True, blank=True)
    data_cumprimento = models.DateField(default=timezone.now)
    data_edicao = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.interno} - {self.data_cumprimento.strftime('%d/%m/%Y')}"





# ocorrencia model

class TipoOcorrencia(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome





class Ocorrencia(models.Model):
    data = models.DateField(default=timezone.now)
    descricao = models.TextField()
    tipo = models.ForeignKey(TipoOcorrencia, on_delete=models.CASCADE)
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE)
    interno = models.ForeignKey(Interno, on_delete=models.CASCADE)
    servidor = models.ForeignKey(Servidor, on_delete=models.CASCADE)
    outros = models.CharField(max_length=100, null=True, blank=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    observacao = models.TextField(null=True, blank=True)
    data_edicao = models.DateTimeField(default=timezone.now)


    def __str__(self):
        return f"{self.descricao} - {self.data.strftime('%d/%m/%Y')}"
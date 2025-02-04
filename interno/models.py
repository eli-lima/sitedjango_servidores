from django.db import models

# Create your models here.


class Interno(models.Model):
    prontuario = models.IntegerField( unique=True)
    nome = models.CharField(max_length=255, db_index=True)
    cpf = models.CharField(max_length=100, blank=True, null=True)
    nome_mae = models.CharField(max_length=255, blank=True, null=True)
    unidade = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    data_extracao = models.DateField()

    def __str__(self):
        return f"{self.nome}"


class ArquivoUpload(models.Model):
    arquivo = models.FileField(upload_to='pdfs/')
    data_upload = models.DateTimeField(auto_now_add=True)
    processado = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.arquivo.name} - {'Processado' if self.processado else 'Pendente'}"

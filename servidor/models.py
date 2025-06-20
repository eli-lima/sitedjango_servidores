from django.db import models
from django.utils.deconstruct import deconstructible
import os
from django.utils import timezone
from django.apps import apps
from django.conf import settings  # Importa as configurações do Django

# Create your models here.
#classe para salvar a foto individualmente

@deconstructible
class PathAndRename:
    def __init__(self, sub_folder):
        self.sub_folder = sub_folder

    def __call__(self, instance, filename):
        # Usa o campo de matrícula para criar uma pasta única para cada servidor
        matricula = instance.matricula
        # Gera o caminho completo onde a imagem será salva
        return os.path.join(self.sub_folder, matricula, filename)


# Instancia a função de caminho de upload
upload_to = PathAndRename('imagens_servidor')


#Listas suspensas servidores
REGIMES = [
        ('estatutario', 'Estatutário'),
        ('prestador', 'Prestador'),
    ]

STATUS = [
        (True, 'Ativo'),
        (False, 'Inativo'),
    ]

GENEROS = [
        ('M', 'Masculino'),
        ('F', 'Feminino'),
        ('O', 'Outro'),
    ]




class Servidor(models.Model):
    matricula = models.CharField(max_length=20, unique=True, blank=False)  # Usando CharField para número de matrícula
    nome = models.CharField(max_length=100, blank=False)  # Nome completo do servidor
    data_nascimento = models.DateField(blank=True, null=True)  # Data de nascimento
    observacao = models.TextField(blank=True, null=True)  # observacao
    disposicao = models.CharField(max_length=100, blank=True, null=True)
    cargo = models.CharField(max_length=100)  # Cargo ou função
    cargo_comissionado = models.CharField(max_length=100, blank=True, null=True)
    simb_cargo_comissionado = models.CharField(max_length=30, blank=True, null=True) #Exemplo csp-1 csp-2
    local_trabalho = models.ForeignKey('seappb.Unidade', on_delete=models.CASCADE)
    genero = models.CharField( max_length=1, choices=GENEROS,)
    lotacao = models.CharField(max_length=50, blank=True, null=True)  # Setor onde o servidor trabalha
    data_admissao = models.DateField(blank=True, null=True)  # Data de admissão
    telefone = models.CharField(max_length=15, blank=True, null=True)  # Número de telefone (opcional)
    email = models.EmailField(max_length=254, blank=True, null=True)  # Email (opcional)
    endereco = models.TextField(blank=True, null=True)  # Endereço (opcional)
    foto_servidor = models.ImageField(upload_to=upload_to, blank=True, null=True)
    regime = models.CharField(
        max_length=50, choices=REGIMES, default='estatutario')   #prestador estatutario
    status = models.BooleanField(max_length=50, choices=STATUS, default='ativo')   #ativa ou afastado por algum motivo

    def save(self, *args, **kwargs):
        Unidade = apps.get_model('seappb', 'Unidade')  # Usando apps.get_model() quando precisar acessar dinamicamente
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome



class ServidorHistory(models.Model):
    servidor = models.ForeignKey(Servidor, on_delete=models.CASCADE)
    campo_alterado = models.CharField(max_length=100)
    valor_antigo = models.TextField(null=True, blank=True)
    valor_novo = models.TextField(null=True, blank=True)
    data_alteracao = models.DateTimeField(auto_now_add=True)

    # Use settings.AUTH_USER_MODEL para referenciar o modelo de usuário
    usuario_responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)


def upload_documento(instance, filename):
    # Define o caminho do arquivo como: 'documentos_servidores/<id_servidor>/<nome_arquivo>'
    return f"documentos_servidores/{instance.servidor.matricula}/{filename}"



class Documento(models.Model):
    servidor = models.ForeignKey(Servidor, related_name="documentos", on_delete=models.CASCADE)
    arquivo = models.FileField(upload_to=upload_documento)
    descricao = models.CharField(max_length=255, blank=True, null=True)  # Descrição opcional do documento
    data_upload = models.DateTimeField(auto_now_add=True)  # Data de upload automático

    @property
    def nome_arquivo(self):
        return os.path.basename(self.arquivo.name)
    def __str__(self):
        return self.descricao if self.descricao else f"Documento de {self.servidor.nome}"
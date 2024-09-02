from django.db import models
from django.utils.deconstruct import deconstructible
import os
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
    data_nascimento = models.DateField()  # Data de nascimento
    cargo = models.CharField(max_length=100)  # Cargo ou função
    cargo_comissionado = models.CharField(max_length=100, blank=True, null=True)
    simb_cargo_comissionado = models.CharField(max_length=30, blank=True, null=True) #Exemplo csp-1 csp-2
    local_trabalho = models.CharField(max_length=100, blank=True, null=True)
    genero = models.CharField( max_length=1, choices=GENEROS,)
    lotacao = models.CharField(max_length=50, blank=True, null=True)  # Setor onde o servidor trabalha
    data_admissao = models.DateField(blank=True, null=True)  # Data de admissão
    telefone = models.CharField(max_length=15, blank=True, null=True)  # Número de telefone (opcional)
    email = models.EmailField(max_length=254, blank=True, null=True)  # Email (opcional)
    endereco = models.TextField(blank=True, null=True)  # Endereço (opcional)
    foto_servidor = models.ImageField(upload_to=upload_to, default='profile_pics/default.jpg')
    regime = models.CharField(
        max_length=50, choices=REGIMES, default='estatutario')   #prestador estatutario
    status = models.BooleanField(max_length=50, choices=STATUS, default='ativo')   #ativa ou afastado por algum motivo
    def __str__(self):
        return self.nome
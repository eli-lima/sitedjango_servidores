from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify

# Create your models here.


class Unidade(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


class Setor(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


# Criar Usuario

def user_directory_path(instance, filename):
    # Extrai a extensão do arquivo original
    ext = filename.split('.')[-1]

    # Cria o nome do arquivo usando a matrícula e o nome completo do usuário
    filename = f'{instance.matricula}_{slugify(instance.nome_completo)}.{ext}'

    # Retorna o caminho para ser usado no Cloudinary (pode adicionar um prefixo se desejar)
    return f'foto_servidores/{instance.matricula}/{filename}'


class Usuario(AbstractUser):
    nome_completo = models.CharField(max_length=200, blank=False)
    foto_perfil = models.ImageField(upload_to=user_directory_path, blank=True, null=True)
    matricula = models.IntegerField(null=True, blank=True)
    setor = models.ForeignKey('Setor', on_delete=models.CASCADE, null=True, blank=True)

    # Remover os campos first_name e last_name
    first_name = None
    last_name = None

    def __str__(self):
        return self.username




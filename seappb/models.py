from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


# class Unidade(models.Model):
#     nome = models.CharField(max_length=100)
#
#     class Meta:
#         db_table = 'seappb_unidade'
#
#     def __str__(self):
#         return self.nome


class Setor(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


# Criar Usuario

class Usuario(AbstractUser):
    nome_completo = models.CharField(max_length=200, blank=False)
    foto_perfil = models.ImageField(upload_to='profile_pics', default='profile_pics/default.jpg')
    matricula = models.IntegerField(null=True, blank=True)
    setor = models.ForeignKey('Setor', on_delete=models.CASCADE, null=True, blank=True)

    # Remover os campos first_name e last_name
    first_name = None
    last_name = None

    def __str__(self):
        return self.username






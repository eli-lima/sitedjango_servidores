from django.db import models
from django.contrib.auth.models import AbstractUser

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


# class Usuario(database.Model, UserMixin):
#     id = database.Column(database.Integer, primary_key=True)
#     nome = database.Column(database.String, nullable=False)
#     sobrenome = database.Column(database.String, nullable=False)
#     matricula = database.Column(database.Integer, nullable=False)
#     email = database.Column(database.String, nullable=False, unique=True)
#     senha = database.Column(database.String, nullable=False)
#     foto_perfil = database.Column(database.String, default='default.jpg')
#     edicoes_adm = database.relationship("Dados_Adm", backref='editor', lazy=True)
#     setor = database.Column(database.String, nullable=False, default='Não Informado')
#     admin = database.Column(database.Boolean, default=False)  # Campo para administrador
#     def contar_edicoes(self):
#         return len(self.edicoes_adm)



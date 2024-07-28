from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


# Criar Usuario

class Usuario(AbstractUser):
    SETOR_CHOICES = [
        ('GESIPE - Administrativo', 'GESIPE - Administrativo'),
        ('GESIPE - SMP', 'GESIPE - SMP'),
        ('GESIPE - Copen', 'GESIPE - Copen'),
    ]

    foto_perfil = models.ImageField(upload_to='profile_pics', default='default.jpg')
    matricula = models.IntegerField(null=True, blank=True)
    setor = models.CharField(max_length=50, choices=SETOR_CHOICES, blank=False, null=False)


    #caso eu queira uma abordagem de muito para muitos
    #edicoes_usuario = models.ManyToManyField('gesipe.Gesipe_admin')

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



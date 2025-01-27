from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from django.core.validators import RegexValidator
import requests

# Create your models here.


# Lista estática de cidades como fallback
CIDADES_FALLBACK = [
    ("João Pessoa", "João Pessoa"),
    ("Campina Grande", "Campina Grande"),
    ("Patos", "Patos"),
    ("Santa Rita", "Santa Rita"),
    ("Bayeux", "Bayeux"),
]

def get_cidades_paraiba():
    """Consulta a API para obter as cidades da Paraíba, com fallback."""
    url = 'https://brasilapi.com.br/api/ibge/municipios/v1/PB'
    try:
        response = requests.get(url, timeout=10)  # Define um timeout para evitar travamentos
        if response.status_code == 200:
            cidades_data = response.json()
            return [(cidade['nome'], cidade['nome']) for cidade in cidades_data]
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar cidades da Paraíba: {e}")

    # Retorna a lista estática como fallback
    return CIDADES_FALLBACK


class Unidade(models.Model):
    nome = models.CharField(max_length=100)
    pais = models.CharField(max_length=255, default='BRASIL')
    estado = models.CharField(max_length=255, default='PARAIBA')
    cidade = models.CharField(
        max_length=255,
        choices=get_cidades_paraiba(),
        blank=True,
        null=True# Carrega as cidades dinamicamente com fallback
    )
    cep = models.CharField(
        max_length=9,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\d{5}-\d{3}$',
                message="O CEP deve estar no formato 12345-678",

            )
        ],
        default='58000-000'
    )
    rua = models.CharField(max_length=255, blank=True, null=True)
    numero = models.CharField(max_length=8, blank=True, null=True)
    complemento = models.CharField(max_length=255, blank=True, null=True)
    reisp = models.IntegerField(choices=[(1, '1° REISP'), (2, '2° REISP'), (3, '3° REISP'), (4, '4° REISP'), (5, '5° REISP')], blank=True, null=True)

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
    return f'profile_pics/{instance.matricula}/{filename}'


class Usuario(AbstractUser):
    nome_completo = models.CharField(max_length=200, blank=False)
    foto_perfil = models.ImageField(upload_to=user_directory_path, blank=True, null=True)
    matricula = models.IntegerField(blank=True, unique=True)
    setor = models.ForeignKey('Setor', on_delete=models.CASCADE, null=True, blank=True)

    # Remover os campos first_name e last_name
    first_name = None
    last_name = None

    # Garantir que o e-mail seja único
    email = models.EmailField(unique=True)  # Adicionando o unique=True para garantir unicidade

    def save(self, *args, **kwargs):
        # Converte o nome completo para maiúsculas
        if self.nome_completo:
            self.nome_completo = self.nome_completo.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username




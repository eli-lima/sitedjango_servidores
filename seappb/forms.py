from django.contrib.auth.forms import UserCreationForm
from .models import Usuario
from django import forms


class CriarContaForm(UserCreationForm):
    email = forms.EmailField()
    foto_perfil = forms.ImageField(required=False)
    matricula = forms.IntegerField(required=False)
    setor = forms.ChoiceField(choices=Usuario.SETOR_CHOICES, required=True)



    class Meta:
        model = Usuario
        fields = ('username', 'email', 'password1', 'password2', 'foto_perfil', 'matricula', 'setor')

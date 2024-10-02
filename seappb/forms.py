from django.contrib.auth.forms import UserCreationForm
from .models import Usuario, Setor
from django import forms


class CriarContaForm(UserCreationForm):
    nome_completo = forms.CharField(max_length=200, required=True)
    email = forms.EmailField()
    foto_perfil = forms.ImageField(required=True)
    matricula = forms.IntegerField(required=True)

    setor = forms.ModelChoiceField(
        queryset=Setor.objects.all(),
        required=False,
        empty_label="Selecione um setor"
    )

    class Meta:
        model = Usuario
        fields = ['username', 'nome_completo', 'email', 'foto_perfil', 'matricula', 'setor', 'password1', 'password2']





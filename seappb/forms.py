from django.contrib.auth.forms import UserCreationForm
from .models import Usuario, Setor, Unidade
from django import forms


class CriarContaForm(UserCreationForm):
    nome_completo = forms.CharField(max_length=200, required=True)
    email = forms.EmailField(required=True)
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




class UnidadeForm(forms.ModelForm):
    class Meta:
        model = Unidade
        fields = [
            'nome', 'pais', 'estado', 'cidade', 'cep', 'rua', 'numero', 'complemento', 'reisp'
        ]

        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'pais': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.Select(attrs={'class': 'form-control'}),
            'cep': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000-000'}),
            'rua': forms.TextInput(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'complemento': forms.TextInput(attrs={'class': 'form-control'}),
            'reisp': forms.Select(attrs={'class': 'form-control'}),
        }

        labels = {
            'nome': 'Nome da Unidade',
            'pais': 'País',
            'estado': 'Estado',
            'cidade': 'Cidade',
            'cep': 'CEP',
            'rua': 'Rua',
            'numero': 'Número',
            'complemento': 'Complemento',
            'reisp': 'REISP',
        }

    def __init__(self, *args, **kwargs):
        super(UnidadeForm, self).__init__(*args, **kwargs)


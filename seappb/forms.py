from django.contrib.auth.forms import UserCreationForm
from .models import Usuario, Unidade
from django import forms
from servidor.models import Servidor
from django.core.exceptions import ValidationError


class CriarContaForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ['username', 'nome_completo', 'email', 'foto_perfil', 'matricula', 'setor', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'nome_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'foto_perfil': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'matricula': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Somente Números...'}),
            'setor': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'username': 'Usuário',
            'nome_completo': 'Nome Completo',
            'email': 'Email',
            'foto_perfil': 'Foto de Perfil',
            'matricula': 'Matrícula',
            'setor': 'Setor',
            'password1': 'Senha Com Letras e Números',
            'password2': 'Confirmar Senha',
        }

    # Definir o queryset para setores dentro do método __init__
    def __init__(self, *args, **kwargs):
        super(CriarContaForm, self).__init__(*args, **kwargs)
        self.fields['setor'].empty_label = 'Selecione seu Setor...'
        self.fields['username'].help_text = ''
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''
        self.fields['password1'].widget = forms.PasswordInput(attrs={'class': 'form-control'})
        self.fields['password2'].widget = forms.PasswordInput(attrs={'class': 'form-control'})

    def clean_matricula(self):
        matricula = self.cleaned_data.get('matricula')

        # Verifica se a matrícula já está associada a um usuário
        if Usuario.objects.filter(matricula=matricula).exists():
            raise ValidationError('Já existe um usuário com esta matrícula.')

        # Verifica se a matrícula corresponde a um servidor existente
        servidor = Servidor.objects.filter(matricula=matricula).first()
        if not servidor:
            raise ValidationError('Nenhum servidor encontrado com esta matrícula.')

        return matricula

    def save(self, commit=True):
        # Cria o usuário como normalmente faria
        usuario = super(CriarContaForm, self).save(commit=False)

        # Associa o usuário ao servidor baseado na matrícula
        matricula = self.cleaned_data.get('matricula')
        servidor = Servidor.objects.get(matricula=matricula)
        usuario.servidor = servidor

        if commit:
            usuario.save()
        return usuario


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


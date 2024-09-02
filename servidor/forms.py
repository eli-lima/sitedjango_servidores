from django.contrib.auth.forms import UserCreationForm
from .models import Servidor
from django import forms



class ServidorForm(forms.ModelForm):
    class Meta:
        model = Servidor
        fields = [
            'matricula', 'nome', 'data_nascimento', 'cargo', 'cargo_comissionado',
            'simb_cargo_comissionado', 'local_trabalho', 'genero', 'lotacao',
            'data_admissao', 'telefone', 'email', 'endereco', 'foto_servidor',
            'regime', 'status'
        ]

        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_admissao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'regime': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'genero': forms.Select(attrs={'class': 'form-control'}),
            'matricula': forms.NumberInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'cargo_comissionado': forms.TextInput(attrs={'class': 'form-control'}),
            'simb_cargo_comissionado': forms.TextInput(attrs={'class': 'form-control'}),
            'local_trabalho': forms.TextInput(attrs={'class': 'form-control'}),
            'lotacao': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(XX) XXXXX-XXXX'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'foto_servidor': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

        labels = {
            'matricula': 'Matrícula',
            'nome': 'Nome Completo',
            'data_nascimento': 'Data de Nascimento',
            'cargo': 'Cargo',
            'cargo_comissionado': 'Cargo Comissionado',
            'simb_cargo_comissionado': 'Símbolo do Cargo Comissionado',
            'local_trabalho': 'Local de Trabalho',
            'genero': 'Gênero',
            'lotacao': 'Lotação',
            'data_admissao': 'Data de Admissão',
            'telefone': 'Telefone',
            'email': 'Email',
            'endereco': 'Endereço',
            'foto_servidor': 'Foto do Servidor',
            'regime': 'Regime de Trabalho',
            'status': 'Status',
        }

    def __init__(self, *args, **kwargs):
        super(ServidorForm, self).__init__(*args, **kwargs)
        # Adicionar classes aos widgets
        self.fields['matricula'].widget.attrs.update(
            {'class': 'form-control'})


class UploadFileForm(forms.Form):
    arquivo_excel = forms.FileField()
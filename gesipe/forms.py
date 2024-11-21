from django import forms
from .models import Gesipe_adm, Gesipe_Sga
from django.forms.widgets import DateInput


class UploadFileForm(forms.Form):
    arquivo_excel = forms.FileField(label='Selecione o arquivo Excel')


class GesipeAdmForm(forms.ModelForm):
    class Meta:
        model = Gesipe_adm
        fields = [
            'data', 'processos', 'diarias', 'documentos_capturados',
            'despachos_gerencias', 'despachos_unidades', 'despachos_grupos',
            'oficios_internos_unidades_prisionais', 'oficios_internos_setores_seap_pb',
            'oficios_internos_circular', 'oficios_externos_seap_pb', 'oficios_externos_judiciario',
            'oficios_externos_diversos', 'os_grupos', 'os_diversos', 'portarias'
        ]
        widgets = {
            'data': forms.DateInput( attrs={
                'class': 'form-control lg:text-base text-xl lg:text-base text-xl', 'placeholder': 'Selecione a data', 'type': 'date'}),
            'processos': forms.NumberInput(attrs={'class': 'form-control lg:text-base text-xl', 'placeholder': '0'}),
            'diarias': forms.NumberInput(attrs={'class': 'form-control lg:text-base text-xl', 'placeholder': '0'}),
            'documentos_capturados': forms.NumberInput(attrs={'class': 'form-control lg:text-base text-xl', 'placeholder': '0'}),
            'portarias': forms.NumberInput(attrs={'class': 'form-control lg:text-base text-xl', 'placeholder': '0'}),
            'despachos_gerencias': forms.NumberInput(attrs={'class': 'form-control lg:text-base text-xl', 'placeholder': '0'}),
            'despachos_unidades': forms.NumberInput(attrs={'class': 'form-control lg:text-base text-xl', 'placeholder': '0'}),
            'despachos_grupos': forms.NumberInput(attrs={'class': 'form-control lg:text-base text-xl', 'placeholder': '0'}),
            'oficios_internos_unidades_prisionais': forms.NumberInput(attrs={'class': 'form-control lg:text-base text-xl', 'placeholder': '0'}),
            'oficios_internos_setores_seap_pb': forms.NumberInput(attrs={'class': 'form-control lg:text-base text-xl', 'placeholder': '0'}),
            'oficios_internos_circular': forms.NumberInput(attrs={'class': 'form-control lg:text-base text-xl', 'placeholder': '0'}),
            'oficios_externos_seap_pb': forms.NumberInput(attrs={'class': 'form-control lg:text-base text-xl', 'placeholder': '0'}),
            'oficios_externos_diversos': forms.NumberInput(attrs={'class': 'form-control lg:text-base text-xl', 'placeholder': '0'}),
            'oficios_externos_judiciario': forms.NumberInput(attrs={'class': 'form-control lg:text-base text-xl', 'placeholder': '0'}),
            'os_grupos': forms.NumberInput(attrs={'class': 'form-control lg:text-base text-xl', 'placeholder': '0'}),
            'os_diversos': forms.NumberInput(attrs={'class': 'form-control lg:text-base text-xl', 'placeholder': '0'}),
        }

        # Adicionando labels personalizados
        labels = {
            'data': 'Data',
            'processos': 'Número de Processos',
            'diarias': 'Diárias',
            'documentos_capturados': 'Documentos Capturados',
            'portarias': 'Número de Portarias',
            'despachos_gerencias': 'Despachos das Gerências',
            'despachos_unidades': 'Despachos das Unidades',
            'despachos_grupos': 'Despachos dos Grupos',
            'oficios_internos_unidades_prisionais': 'Ofícios Internos (Unidades Prisionais)',
            'oficios_internos_setores_seap_pb': 'Ofícios Internos (Setores SEAP PB)',
            'oficios_internos_circular': 'Ofícios Internos (Circular)',
            'oficios_externos_seap_pb': 'Ofícios Externos (SEAP PB)',
            'oficios_externos_diversos': 'Ofícios Externos (Diversos)',
            'oficios_externos_judiciario': 'Ofícios Externos (Judiciário)',
            'os_grupos': 'Ordens de Serviço (Grupos)',
            'os_diversos': 'Ordens de Serviço (Diversos)',
        }


class GesipeSgaForm(forms.ModelForm):
    class Meta:
        model = Gesipe_Sga
        fields = [
            'data', 'agendamentos_entradas', 'comunicacoes_presos', 'comunicacoes_servidores',
            'comunicacoes_setores', 'comunicacoes_judiciais_externas', 'om_grupos',
            'om_unidades'
        ]
        widgets = {
            'data': forms.DateInput( attrs={
                'class': 'form-control lg:text-base text-xl lg:text-base text-xl', 'placeholder': 'Selecione a data', 'type': 'date'}),
            'agendamentos_entradas': forms.NumberInput(attrs={'class': 'form-control lg:text-base text-xl', 'placeholder': '0'}),
            'comunicacoes_presos': forms.NumberInput(attrs={'class': 'form-control lg:text-base text-xl', 'placeholder': '0'}),
            'comunicacoes_servidores': forms.NumberInput(attrs={'class': 'form-control lg:text-base text-xl', 'placeholder': '0'}),
            'comunicacoes_setores': forms.NumberInput(attrs={'class': 'form-control lg:text-base text-xl', 'placeholder': '0'}),
            'comunicacoes_judiciais_externas': forms.NumberInput(attrs={'class': 'form-control lg:text-base text-xl', 'placeholder': '0'}),
            'om_grupos': forms.NumberInput(attrs={'class': 'form-control lg:text-base text-xl', 'placeholder': '0'}),
            'om_unidades': forms.NumberInput(attrs={'class': 'form-control lg:text-base text-xl', 'placeholder': '0'}),

        }

        # Adicionando labels personalizados
        labels = {
            'data': 'Data',
            'agendamentos_entradas': 'Agendamentos Entradas',
            'comunicacoes_presos': 'Comunicações - Presos',
            'comunicacoes_servidores': 'Comunicações - Servidores',
            'comunicacoes_setores': 'Comunicações - Setores',
            'comunicacoes_judiciais_externas': 'Comunicações - Judiciais e Externas',
            'om_grupos': 'Ordens de Missão - Grupos',
            'om_unidades': 'Ordens de Missão - Unidades',

        }


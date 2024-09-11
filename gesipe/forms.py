from django import forms
from .models import Gesipe_adm
from django.forms.widgets import DateInput


# class BuscaDataForm(forms.Form):
#     data = forms.DateField(
#         widget=DateInput(format='%d/%m/%Y', attrs={'class': 'form-control lg:text-base text-xl', 'placeholder': 'dd/mm/yyyy'}),
#         input_formats=['%d/%m/%Y']
#     )
#




class GesipeAdmForm(forms.ModelForm):
    class Meta:
        model = Gesipe_adm
        fields = [
            'data', 'processos', 'memorandos_diarias', 'memorandos_documentos_capturados',
            'despachos_gerencias', 'despachos_unidades', 'despachos_grupos',
            'oficios_internos_unidades_prisionais', 'oficios_internos_setores_seap_pb',
            'oficios_internos_circular', 'oficios_externos_seap_pb', 'oficios_externos_judiciario',
            'oficios_externos_diversos', 'os_grupos', 'os_diversos', 'portarias'
        ]
        widgets = {
            'data': forms.DateInput( attrs={
                'class': 'form-control lg:text-base text-xl lg:text-base text-xl', 'placeholder': 'Selecione a data', 'type': 'date'}),
            'processos': forms.NumberInput(attrs={'class': 'form-control lg:text-base text-xl', 'placeholder': '0'}),
            'memorandos_diarias': forms.NumberInput(attrs={'class': 'form-control lg:text-base text-xl', 'placeholder': '0'}),
            'memorandos_documentos_capturados': forms.NumberInput(attrs={'class': 'form-control lg:text-base text-xl', 'placeholder': '0'}),
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
            'memorandos_diarias': 'Memorandos de Diárias',
            'memorandos_documentos_capturados': 'Memorandos de Documentos Capturados',
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
from django import forms
from .models import Gesipe_adm
from django.forms.widgets import DateInput


class BuscaDataForm(forms.Form):
    data = forms.DateField(
        widget=DateInput(format='%d/%m/%Y', attrs={'class': 'form-control', 'placeholder': 'dd/mm/yyyy'}),
        input_formats=['%d/%m/%Y']
    )





class GesipeAdmForm(forms.ModelForm):
    class Meta:
        model = Gesipe_adm
        fields = ['data', 'processos', 'memorandos_diarias', 'memorandos_documentos_capturados',
                  'portarias', 'despachos_gerencias', 'despachos_unidades', 'despachos_grupos',
                  'oficios_internos_unidades_prisionais', 'oficios_internos_setores_seap_pb',
                  'oficios_internos_circular', 'oficios_externos_seap_pb', 'oficios_externos_diversos',
                  'oficios_externos_judiciario', 'os_grupos', 'os_diversos']

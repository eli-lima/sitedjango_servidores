# forms.py
from django import forms
from .models import Ajuda_Custo
import datetime
from seappb.models import Unidade


MESES = [
    ('', '--- Selecione um Mês ---'),
    ('01', 'Janeiro'),
    ('02', 'Fevereiro'),
    ('03', 'Março'),
    ('04', 'Abril'),
    ('05', 'Maio'),
    ('06', 'Junho'),
    ('07', 'Julho'),
    ('08', 'Agosto'),
    ('09', 'Setembro'),
    ('10', 'Outubro'),
    ('11', 'Novembro'),
    ('12', 'Dezembro'),
]

ANOS = [('', '--- Selecione um Ano ---')] + [(str(year), str(year)) for year in range(2023, datetime.datetime.now().year + 2)]

DIAS = [(str(day), str(day)) for day in range(1, 32)]


class AjudaCustoForm(forms.ModelForm):
    unidade = forms.ChoiceField(
        choices=[('', '--- Selecione uma unidade ---')])
    dia = forms.ChoiceField(choices=DIAS, required=True)
    mes = forms.ChoiceField(choices=MESES, required=True)
    ano = forms.ChoiceField(choices=ANOS, required=True)

    class Meta:
        model = Ajuda_Custo
        fields = ['unidade', 'carga_horaria']

    def clean(self):
        cleaned_data = super().clean()
        dia = cleaned_data.get('dia')
        mes = cleaned_data.get('mes')
        ano = cleaned_data.get('ano')

        # Combina o dia, mês e ano para formar uma data
        try:
            data = datetime.date(int(ano), int(mes), int(dia))
            cleaned_data['data'] = data
        except ValueError:
            raise forms.ValidationError('Data inválida. Verifique o dia, mês e ano selecionados.')

        return cleaned_data
# forms.py
from django import forms
from .models import Ajuda_Custo, LimiteAjudaCusto
import datetime
from seappb.models import Unidade
from django.core.exceptions import ValidationError


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


def get_mes_field():
    return forms.ChoiceField(choices=MESES, required=True)

def get_ano_field():
    return forms.ChoiceField(choices=ANOS, required=True)

def get_unidade_field():
    return forms.ChoiceField(
        choices=[('', '--- Selecione uma unidade ---')] + [(u.nome, u.nome) for u in Unidade.objects.all()]
    )

class AjudaCustoForm(forms.ModelForm):
    unidade = get_unidade_field()
    dia = forms.ChoiceField(choices=DIAS, required=True)
    mes = get_mes_field()
    ano = get_ano_field()
    folha_assinada = forms.FileField(required=True)  # Campo de upload para a folha assinada

    class Meta:
        model = Ajuda_Custo
        fields = ['unidade', 'carga_horaria', 'folha_assinada']

    def clean_folha_assinada(self):
        folha_assinada = self.cleaned_data.get('folha_assinada')

        # Se o arquivo for enviado, faça as verificações
        if folha_assinada:
            if folha_assinada.size > 10 * 1024 * 1024:
                raise forms.ValidationError("O arquivo deve ter no máximo 10MB.")
            if not folha_assinada.content_type in ['application/pdf', 'image/jpeg', 'image/jpg']:
                raise forms.ValidationError("Apenas arquivos PDF ou JPG são permitidos.")
        return folha_assinada

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


class AdminDatasForm(forms.Form):
    matricula = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Somente Números...', 'id': 'matricula'}),
        required=True
    )
    mes = get_mes_field()
    ano = get_ano_field()
    unidade = get_unidade_field()
    dias_12h = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Dias separados por vírgulas...', 'id': 'dias_12h'}),
        required=False
    )
    dias_24h = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Dias separados por vírgulas...', 'id': 'dias_24h'}),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adiciona IDs aos campos para uso no JavaScript
        self.fields['mes'].widget.attrs.update({'id': 'mes'})
        self.fields['ano'].widget.attrs.update({'id': 'ano'})
        self.fields['unidade'].widget.attrs.update({'id': 'unidade'})


class LimiteAjudaCustoForm(forms.ModelForm):
    class Meta:
        model = LimiteAjudaCusto
        fields = ['servidor', 'limite_horas']

        # Defina os widgets para adicionar o placeholder
        widgets = {
            'limite_horas': forms.NumberInput(attrs={'placeholder': 'Digite o limite em horas'}),
            'servidor': forms.Select(attrs={'placeholder': 'Selecione o servidor'}),
        }
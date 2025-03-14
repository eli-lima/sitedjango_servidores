# forms.py
from django import forms
from .models import Ajuda_Custo, LimiteAjudaCusto, CotaAjudaCusto
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


def get_unidade_choices():
    # Mova a lógica de consulta para uma função separada
    return [('', '--- Selecione uma unidade ---')] + [(u.nome, u.nome) for u in Unidade.objects.all().order_by('nome')]



class EnvioDatasForm(forms.ModelForm):
    unidade = forms.ChoiceField(choices=[], required=True)
    dia = forms.ChoiceField(choices=DIAS, required=True)
    mes = get_mes_field()
    ano = get_ano_field()

    class Meta:
        model = Ajuda_Custo
        fields = ['ano', 'dia', 'mes', 'unidade', 'carga_horaria']

    def __init__(self, *args, **kwargs):
        super(EnvioDatasForm, self).__init__(*args, **kwargs)
        self.fields['unidade'].choices = get_unidade_choices()

        self.fields['dia'].label = 'Dia'
        self.fields['dia'].widget.attrs.update({'class': 'form-control xl:text-base text-2xl'})

        self.fields['mes'].label = 'Mês'
        self.fields['mes'].widget.attrs.update({'class': 'form-control xl:text-base text-2xl'})

        self.fields['ano'].label = 'Ano'
        self.fields['ano'].widget.attrs.update({'class': 'form-control xl:text-base text-2xl'})

        self.fields['unidade'].label = 'Unidade de Trabalho'
        self.fields['unidade'].widget.attrs.update({'class': 'form-control xl:text-base text-2xl'})

        self.fields['carga_horaria'].label = 'Horas'
        self.fields['carga_horaria'].widget.attrs.update({'class': 'form-control xl:text-base text-2xl'})

    def clean(self):
        cleaned_data = super().clean()
        dia = cleaned_data.get('dia')
        mes = cleaned_data.get('mes')
        ano = cleaned_data.get('ano')

        try:
            data = datetime.date(int(ano), int(mes), int(dia))
            cleaned_data['data'] = data
        except ValueError:
            raise forms.ValidationError('Data inválida. Verifique o dia, mês e ano selecionados.')

        return cleaned_data


class ConfirmacaoDatasForm(forms.Form):
    codigo_verificacao = forms.CharField(max_length=6, label='Código de Verificação', required=False)


class AdminDatasForm(forms.Form):
    matricula = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Somente Números...', 'id': 'matricula'}),
        required=True
    )
    mes = get_mes_field()
    ano = get_ano_field()
    unidade = forms.ChoiceField(choices=[], required=True)  # Inicialmente vazio
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

        # Preencha as escolhas do campo unidade
        self.fields['unidade'].choices = get_unidade_choices()

        # Adiciona IDs e classes aos campos para uso no JavaScript
        self.fields['mes'].label = 'Mês'
        self.fields['mes'].widget.attrs.update({'id': 'mes', 'class': 'form-control xl:text-base text-2xl'})

        self.fields['ano'].label = 'Ano'
        self.fields['ano'].widget.attrs.update({'id': 'ano', 'class': 'form-control xl:text-base text-2xl'})

        self.fields['unidade'].label = 'Unidade'
        self.fields['unidade'].widget.attrs.update({'id': 'unidade', 'class': 'form-control xl:text-base text-2xl'})

        self.fields['matricula'].label = 'Matrícula'
        self.fields['matricula'].widget.attrs.update({'id': 'matricula', 'class': 'form-control xl:text-base text-2xl'})

        self.fields['dias_12h'].label = 'Dias 12 Horas'
        self.fields['dias_12h'].widget.attrs.update({'id': 'dias_12h', 'class': 'form-control xl:text-base text-2xl'})

        self.fields['dias_24h'].label = 'Dias 24 Horas'
        self.fields['dias_24h'].widget.attrs.update({'id': 'dias_24h', 'class': 'form-control xl:text-base text-2xl'})


class LimiteAjudaCustoForm(forms.ModelForm):
    class Meta:
        model = LimiteAjudaCusto
        fields = ['servidor', 'unidade', 'limite_horas']  # Inclua o campo unidade

        # Defina os widgets para adicionar o placeholder
        widgets = {
            'limite_horas': forms.NumberInput(attrs={'placeholder': 'Digite o limite em horas'}),
            'servidor': forms.Select(attrs={'placeholder': 'Selecione o servidor'}),
            'unidade': forms.Select(attrs={'placeholder': 'Selecione a unidade'})  # Adicione o widget para unidade
        }

    def __init__(self, *args, **kwargs):
        super(LimiteAjudaCustoForm, self).__init__(*args, **kwargs)
        # Ordena a lista de servidores por nome
        self.fields['servidor'].queryset = self.fields['servidor'].queryset.order_by('nome')
        # Ordena a lista de unidades por nome
        self.fields['unidade'].queryset = self.fields['unidade'].queryset.order_by('nome')


class GerenteAjudaCustoForm(forms.ModelForm):
    class Meta:
        model = LimiteAjudaCusto
        fields = ['servidor', 'unidade', 'limite_horas']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['unidade'].disabled = True


class CotaAjudaCustoForm(forms.ModelForm):
    class Meta:
        model = CotaAjudaCusto
        fields = ['gestor', 'unidade', 'cota_ajudacusto']
        widgets = {
            'gestor': forms.Select(attrs={'class': 'form-control'}),
            'unidade': forms.Select(attrs={'class': 'form-control'}),
            'cota_ajudacusto': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'gestor': 'Gestor',
            'unidade': 'Unidade',
            'cota_ajudacusto': 'Cota de Ajuda de Custo (em dias)',
        }

#carregar relatorio rx2

class UploadExcelRx2Form(forms.Form):
    file = forms.FileField(label='Selecione o arquivo Excel')


#envio de codigo para o email



class VerificacaoForm(forms.Form):
    codigo_verificacao = forms.CharField(max_length=8, required=True, label='Código de Verificação')


class FiltroRelatorioForm(forms.Form):
    unidade = forms.ChoiceField(
        choices=[],  # As opções serão preenchidas no método __init__
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Unidade"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Obtém as unidades disponíveis no banco de dados
        unidades = Ajuda_Custo.objects.values_list('unidade', flat=True).distinct().order_by('unidade')
        # Define as opções do campo unidade
        self.fields['unidade'].choices = [("", "Selecione uma Unidade...")] + [(u, u) for u in unidades]

from django import forms
from servidor.models import Servidor
from seappb.models import Unidade
from .models import OcorrenciaPlantao
from interno.models import PopulacaoCarceraria


# forms.py


class OcorrenciaPlantaoForm(forms.Form):
    # Campos principais

    data = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label="Data do Plantão"
    )

    chefe_equipe = forms.ModelChoiceField(
        queryset=Servidor.objects.all().order_by('nome'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Chefe de Equipe",
        empty_label="Servidor..."
    )

    # Campo unidade será preenchido automaticamente e não editável
    unidade = forms.ModelChoiceField(
        queryset=Unidade.objects.all().order_by('nome'),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'readonly': 'readonly',
            'disabled': 'disabled'
        }),
        label="Unidade",
        required=False
    )

    descricao = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Descreva o plantão...'
        }),
        label="Descrição do Plantão"
    )

    # Campo observação não obrigatório
    observacao = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Observações no Plantão...'
        }),
        label="Observações do Plantão",
        required=False  # Tornando o campo não obrigatório
    )


    ordinario_ids = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )

    extraordinario_ids = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )



    # População carcerária
    regime_aberto = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0'
        }),
        label="Aberto",
        initial=0
    )

    regime_semiaberto = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0'
        }),
        label="Semiaberto",
        initial=0
    )

    regime_fechado = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0'
        }),
        label="Fechado",
        initial=0
    )

    regime_domiciliar = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0'
        }),
        label="Domiciliar",
        initial=0
    )

    provisorio = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0'
        }),
        label="Provisórios",
        initial=0
    )

    sentenciado = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0'
        }),
        label="Sentenciados",
        initial=0
    )

    masculino = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0'
        }),
        label="Masculino",
        initial=0
    )

    feminino = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0'
        }),
        label="Feminino",
        initial=0
    )

    # Observações
    observacoes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observações adicionais...'
        }),
        required=False,
        label="Observações"
    )

    def clean(self):
        cleaned_data = super().clean()

        # Processar IDs dos servidores ordinários
        ordinario_ids = [id for id in cleaned_data.get('ordinario_ids', '').split(',') if id]
        if not ordinario_ids:
            self.add_error(None, "Adicione pelo menos um servidor ordinário")

        # Processar IDs dos servidores extraordinários
        extraordinario_ids = [id for id in cleaned_data.get('extraordinario_ids', '').split(',') if id]

        # Adiciona os querysets processados ao cleaned_data
        cleaned_data['servidores_ordinario'] = Servidor.objects.filter(id__in=ordinario_ids)
        cleaned_data['servidores_extraordinario'] = Servidor.objects.filter(id__in=extraordinario_ids)

        return cleaned_data

    def save(self, user):
        cleaned_data = self.cleaned_data
        unidade = user.servidor.local_trabalho


        # Criar ocorrência de plantão
        plantao = OcorrenciaPlantao.objects.create(
            data=cleaned_data['data'],
            unidade=unidade,
            chefe_equipe=cleaned_data['chefe_equipe'],
            descricao=cleaned_data['descricao'],
            observacao=cleaned_data.get('observacao', ''),  # Campo não obrigatório
            usuario=user
        )

        # Adicionar servidores
        plantao.servidores_ordinario.set(cleaned_data['servidores_ordinario'])
        plantao.servidores_extraordinario.set(cleaned_data['servidores_extraordinario'])

        # Criar população carcerária
        PopulacaoCarceraria.objects.create(
            plantao=plantao,  # <-- esse campo precisa existir no modelo!
            data_atualizacao=cleaned_data['data'],
            unidade=unidade,
            regime_aberto=cleaned_data['regime_aberto'],
            regime_semiaberto=cleaned_data['regime_semiaberto'],
            regime_fechado=cleaned_data['regime_fechado'],
            regime_domiciliar=cleaned_data['regime_domiciliar'],
            provisorio=cleaned_data['provisorio'],
            sentenciado=cleaned_data['sentenciado'],
            masculino=cleaned_data['masculino'],
            feminino=cleaned_data['feminino'],
            usuario=user
        )

        return plantao




# class ApreensaoForm(forms.ModelForm):
#     class Meta:
#         model = Apreensao
#         fields = ['data', 'natureza', 'objeto', 'unidade', 'quantidade', 'descricao', 'observacao']
#
#         widgets = {
#             'data': forms.DateInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Selecione a data',
#                 'type': 'date'
#             }),
#             'quantidade': forms.NumberInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Informe a quantidade'
#             }),
#             'unidade': forms.Select(attrs={
#                 'class': 'form-select',
#             }),
#             'descricao': forms.Textarea(attrs={
#                 'class': 'form-control',
#                 'rows': 3,
#                 'placeholder': 'Descreva a ocorrência'
#             }),
#             'observacao': forms.Textarea(attrs={
#                 'class': 'form-control',
#                 'rows': 3,
#                 'placeholder': 'Adicione observações adicionais'
#             }),
#         }
#
#     # Campo para busca do natureza
#     natureza = forms.ModelChoiceField(
#         queryset=Natureza.objects.all(),
#         widget=forms.Select(attrs={
#             'class': 'form-control',
#             'hx-get': '/copen/filtrar-objetos/',
#             'hx-target': '#id_objeto',
#             'hx-trigger': 'change',
#         })
#     )
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#
#         # Ordena as unidades em ordem alfabética
#         self.fields['unidade'].queryset = self.fields['unidade'].queryset.order_by(
#             'nome')  # Substitua 'nome_da_unidade' pelo nome do campo de unidade
#
#
# class OcorrenciaForm(forms.ModelForm):
#     class Meta:
#         model = Ocorrencia
#         fields = ['data', 'descricao', 'tipo', 'unidade', 'servidor', 'outros', 'observacao']
#
#         widgets = {
#             'data': forms.DateInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Selecione a data',
#                 'type': 'date'
#             }),
#             'descricao': forms.Textarea(attrs={
#                 'class': 'form-control',
#                 'rows': 3,
#                 'placeholder': 'Descreva a ocorrência'
#             }),
#             'tipo': forms.Select(attrs={
#                 'class': 'form-select',
#             }),
#             'servidor': forms.Select(attrs={
#                 'class': 'form-select',
#                 'required': False
#             }),
#             'unidade': forms.Select(attrs={
#                 'class': 'form-select',
#                 'required': False
#             }),
#             'outros': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Em Caso de Outros Envolvidos'
#             }),
#             'observacao': forms.Textarea(attrs={
#                 'class': 'form-control',
#                 'rows': 3,
#                 'placeholder': 'Adicione observações adicionais'
#             }),
#         }
#
#     # Campo para busca do interno
#     interno_nome = forms.CharField(
#         required=False,
#         widget=forms.TextInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Digite o nome ou prontuário do interno',
#             'hx-get': '/copen/buscar-interno/',
#             'hx-trigger': 'keyup changed delay:500ms',
#             'hx-target': '#autocomplete-results',
#             'hx-indicator': '#autocomplete-loading',
#
#         })
#     )
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#
#         self.fields['servidor'].empty_label = "Selecione um servidor"  # Define o texto padrão
#         self.fields['unidade'].empty_label = "Selecione uma Unidade"  # Define o texto padrão
#
#
#         # Ordena as unidades em ordem alfabética
#         self.fields['unidade'].queryset = self.fields['unidade'].queryset.order_by(
#             'nome')  # Substitua 'nome_da_unidade' pelo nome do campo de unidade
#
#
# #campos de custodia
#
# class CustodiaForm(forms.ModelForm):
#     class Meta:
#         model = Custodia
#         fields = [
#              'unidade_hospitalar', 'unidade_solicitante',
#             'responsavel', 'observacao', 'data_entrada', 'data_saida'
#         ]
#         widgets = {
#
#             'unidade_hospitalar': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Nome do hospital'
#             }),
#             'unidade_solicitante': forms.Select(attrs={
#                 'class': 'form-control'
#             }),
#             'responsavel': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Nome do responsável'
#             }),
#             'observacao': forms.Textarea(attrs={
#                 'class': 'form-control',
#                 'rows': 3,
#                 'placeholder': 'Adicione observações'
#             }),
#             'data_entrada': forms.DateInput(attrs={
#                 'class': 'form-control',
#                 'type': 'date',
#                 'placeholder': 'Selecione a data de entrada'
#             }),
#             'data_saida': forms.DateInput(attrs={
#                 'class': 'form-control',
#                 'type': 'date',
#                 'placeholder': 'Selecione a data de saída (opcional)'
#             }),
#         }
#
#     # Campo para busca do interno
#     interno_nome = forms.CharField(
#         required=False,
#         widget=forms.TextInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Digite o nome ou prontuário do interno',
#             'hx-get': '/copen/buscar-interno/',
#             'hx-trigger': 'keyup changed delay:500ms',
#             'hx-target': '#autocomplete-results',
#             'hx-indicator': '#autocomplete-loading',
#         })
#     )
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#
#         # Ordena as unidades em ordem alfabética
#         self.fields['unidade_solicitante'].queryset = self.fields['unidade_solicitante'].queryset.order_by(
#             'nome')  # Substitua 'nome_da_unidade' pelo nome do campo de unidade
# class CustodiaEditForm(forms.ModelForm):
#     class Meta:
#         model = Custodia
#         fields = ['data_saida', 'responsavel', 'observacao',]  # Inclui apenas o campo que será editado
#         widgets = {
#             'data_saida': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
#             'responsavel': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Nome do responsável'
#             }),
#             'observacao': forms.Textarea(attrs={
#                 'class': 'form-control',
#                 'rows': 3,
#                 'placeholder': 'Adicione observações'
#             }),
#         }
#
#
# #campos de mandado de prisao
#
#
#
#
# class MpForm(forms.ModelForm):
#     class Meta:
#         model = Mp
#         fields = ['tipo', 'nome_mae', 'unidade', 'data_cumprimento', 'observacao']
#
#         widgets = {
#
#             'tipo': forms.Select(attrs={
#                 'class': 'form-select',
#             }),
#             'nome_mae': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Nome do responsável',
#                 'readonly': 'readonly',  # Torna o campo não editável
#                 'id': 'id_nome_mae',  # Adicione um ID para o campo
#             }),
#             'unidade': forms.Select(attrs={
#                 'class': 'form-select',
#             }),
#
#             'data_cumprimento': forms.DateInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Selecione a data',
#                 'type': 'date',
#                 'id' : 'id_data_cumprimento'
#             }),
#             'observacao': forms.Textarea(attrs={
#                 'class': 'form-control',
#                 'rows': 3,
#                 'placeholder': 'Adicione observações adicionais'
#             }),
#         }
#
#     # Campo para busca do interno
#     interno_nome = forms.CharField(
#         required=False,
#         widget=forms.TextInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Digite o nome ou prontuário do interno',
#             'hx-get': '/copen/buscar-interno/',
#             'hx-trigger': 'keyup changed delay:500ms',
#             'hx-target': '#autocomplete-results',
#             'hx-indicator': '#autocomplete-loading',
#         })
#     )
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#
#         self.fields['tipo'].empty_label = "Selecione o Tipo de MP..."  # Define o texto padrão
#         self.fields['unidade'].empty_label = "Selecione a Unidade de Cumprimento..."  # Define o texto padrão
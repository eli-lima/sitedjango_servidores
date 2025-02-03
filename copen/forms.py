from django import forms
from .models import (Apreensao, Natureza, Objeto,
                     Ocorrencia, Atendimento, Custodia,
                     Mp)


class AtendimentoForm(forms.ModelForm):
    localizado = forms.ChoiceField(
        choices=[(True, "Localizado"), (False, "Não localizado")],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Resultado"
    )

    class Meta:
        model = Atendimento
        fields = [
            'data', 'servidor', 'outros', 'nome', 'localizado',
            'matricula', 'instituicao', 'unidade', 'observacao'
        ]
        widgets = {
            'data': forms.DateInput(attrs={
                'class': 'form-control',
                'placeholder': 'Selecione a data',
                'type': 'date'
            }),
            'servidor': forms.Select(attrs={'class': 'form-select'}),
            'outros': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Outras informações'
            }),
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome Pesquisado'
            }),
            'matricula': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite a matrícula'
            }),
            'instituicao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite o nome da instituição'
            }),
            'unidade': forms.Select(attrs={'class': 'form-select'}),
            'observacao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Adicione observações'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['servidor'].empty_label = "Selecione um servidor"
        self.fields['unidade'].empty_label = "Selecione a Unidade ou Regime se Localizado..."






class ApreensaoForm(forms.ModelForm):
    class Meta:
        model = Apreensao
        fields = ['data', 'natureza', 'objeto', 'unidade', 'quantidade', 'descricao', 'observacao']

        widgets = {
            'data': forms.DateInput(attrs={
                'class': 'form-control',
                'placeholder': 'Selecione a data',
                'type': 'date'
            }),
            'quantidade': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Informe a quantidade'
            }),
            'unidade': forms.Select(attrs={
                'class': 'form-select',
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descreva a ocorrência'
            }),
            'observacao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Adicione observações adicionais'
            }),
        }

    # Campo para busca do natureza
    natureza = forms.ModelChoiceField(
        queryset=Natureza.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'hx-get': '/copen/filtrar-objetos/',
            'hx-target': '#id_objeto',
            'hx-trigger': 'change',
        })
    )


class OcorrenciaForm(forms.ModelForm):
    class Meta:
        model = Ocorrencia
        fields = ['data', 'descricao', 'tipo', 'unidade', 'servidor', 'outros', 'observacao']

        widgets = {
            'data': forms.DateInput(attrs={
                'class': 'form-control',
                'placeholder': 'Selecione a data',
                'type': 'date'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descreva a ocorrência'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select',
            }),
            'servidor': forms.Select(attrs={
                'class': 'form-select',
            }),
            'unidade': forms.Select(attrs={
                'class': 'form-select',
            }),
            'outros': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Em Caso de Outros Envolvidos'
            }),
            'observacao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Adicione observações adicionais'
            }),
        }

    # Campo para busca do interno
    interno_nome = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite o nome ou prontuário do interno',
            'hx-get': '/copen/buscar-interno/',
            'hx-trigger': 'keyup changed delay:500ms',
            'hx-target': '#autocomplete-results',
            'hx-indicator': '#autocomplete-loading',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['servidor'].empty_label = "Selecione um servidor"  # Define o texto padrão
        self.fields['unidade'].empty_label = "Selecione uma Unidade"  # Define o texto padrão


#campos de custodia



class CustodiaForm(forms.ModelForm):
    class Meta:
        model = Custodia
        fields = [
             'unidade_hospitalar', 'unidade_solicitante',
            'responsavel', 'observacao', 'data_entrada', 'data_saida'
        ]
        widgets = {

            'unidade_hospitalar': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do hospital'
            }),
            'unidade_solicitante': forms.Select(attrs={
                'class': 'form-control'
            }),
            'responsavel': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do responsável'
            }),
            'observacao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Adicione observações'
            }),
            'data_entrada': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'Selecione a data de entrada'
            }),
            'data_saida': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'Selecione a data de saída (opcional)'
            }),
        }

    # Campo para busca do interno
    interno_nome = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite o nome ou prontuário do interno',
            'hx-get': '/copen/buscar-interno/',
            'hx-trigger': 'keyup changed delay:500ms',
            'hx-target': '#autocomplete-results',
            'hx-indicator': '#autocomplete-loading',
        })
    )


class CustodiaEditForm(forms.ModelForm):
    class Meta:
        model = Custodia
        fields = ['data_saida']  # Inclui apenas o campo que será editado
        widgets = {
            'data_saida': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


#campos de mandado de prisao




class MpForm(forms.ModelForm):
    class Meta:
        model = Mp
        fields = ['tipo', 'nome_mae', 'unidade', 'data_cumprimento', 'observacao']

        widgets = {

            'tipo': forms.Select(attrs={
                'class': 'form-select',
            }),
            'nome_mae': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do responsável',
                'readonly': 'readonly',  # Torna o campo não editável
                'id': 'id_nome_mae',  # Adicione um ID para o campo
            }),
            'unidade': forms.Select(attrs={
                'class': 'form-select',
            }),

            'data_cumprimento': forms.DateInput(attrs={
                'class': 'form-control',
                'placeholder': 'Selecione a data',
                'type': 'date',
                'id' : 'id_data_cumprimento'
            }),
            'observacao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Adicione observações adicionais'
            }),
        }

    # Campo para busca do interno
    interno_nome = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite o nome ou prontuário do interno',
            'hx-get': '/copen/buscar-interno/',
            'hx-trigger': 'keyup changed delay:500ms',
            'hx-target': '#autocomplete-results',
            'hx-indicator': '#autocomplete-loading',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['tipo'].empty_label = "Selecione o Tipo de MP..."  # Define o texto padrão
        self.fields['unidade'].empty_label = "Selecione a Unidade de Cumprimento..."  # Define o texto padrão
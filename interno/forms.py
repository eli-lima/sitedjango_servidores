from django import forms
from .models import PopulacaoCarceraria


class UploadExcelInternosForm(forms.Form):
    arquivo = forms.FileField(label="Upload de Planilha (.xlsx)")


class PopulacaoCarcerariaForm(forms.ModelForm):
    class Meta:
        model = PopulacaoCarceraria
        fields = ['unidade', 'regime_aberto', 'regime_semiaberto',
                  'regime_fechado', 'regime_domiciliar', 'provisorio', 'sentenciado',
                  'masculino', 'sentenciado', 'total'
                  ]

        widgets = {
            'unidade': forms.Select(attrs={
                'class': 'form-select',
            }),

            'regime_aberto': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'População Aberto...'
            }),
            'regime_semiaberto': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'População SemiAberto...'
            }),
            'regime_fechado': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'População Fechado...'
            }),
            'regime_domiciliar': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'População Domiciliar...'
            }),
            'provisorio': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Provisórios...'
            }),
            'sentenciado': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Sentenciados...'
            }),
            'masculino': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Masculino...'
            }),
            'feminino': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Feminino...'
            }),
            'total': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'total...'
            }),

        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Pega o usuário passado pela view
        super().__init__(*args, **kwargs)

        self.fields['unidade'].empty_label = "Selecione uma Unidade"
        self.fields['unidade'].queryset = self.fields['unidade'].queryset.order_by('nome')

        if user:
            grupos_admin = ['Administrador', 'GerGesipe']
            pode_editar_unidade = user.groups.filter(name__in=grupos_admin).exists()

            if not pode_editar_unidade:
                # Se o usuário não pode editar, desabilita o campo
                self.fields['unidade'].disabled = True

            # Sempre, para todos usuários, inicializa o campo unidade com o local de trabalho
            self.initial['unidade'] = user.servidor.local_trabalho


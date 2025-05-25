from django import forms
from .models import Armamento, MovimentacaoMunicao, LoteMunicao, EstoqueMunicao, BaixaMunicao
from django.core.exceptions import ValidationError
from django.utils import timezone
from servidor.models import Servidor
from seappb.models import Unidade

class ArmamentoForm(forms.ModelForm):
    class Meta:
        model = Armamento
        fields = ['tipo_arma', 'calibre', 'marca', 'modelo', 'numero_serie',
                  'servidor', 'unidade', 'observacao', 'status']

        widgets = {
            'tipo_arma': forms.Select(attrs={
                'class': 'form-select block w-full mt-1',
            }),
            'calibre': forms.Select(attrs={
                'class': 'form-select block w-full mt-1',
            }),
            'marca': forms.Select(attrs={
                'class': 'form-select block w-full mt-1',
            }),
            'modelo': forms.Select(attrs={
                'class': 'form-select block w-full mt-1',
            }),
            'servidor': forms.Select(attrs={
                'class': 'form-select block w-full mt-1',
            }),
            'unidade': forms.Select(attrs={
                'class': 'form-select block w-full mt-1',
            }),
            'numero_serie': forms.TextInput(attrs={
                'class': 'form-input block w-full mt-1',
                'placeholder': 'Ex: ABC123456'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select block w-full mt-1',
            }),
            'observacao': forms.Textarea(attrs={
                'class': 'form-textarea block w-full mt-1',
                'rows': 3,
                'placeholder': 'Informações adicionais sobre o armamento...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Configurações de placeholders e labels
        self.fields['unidade'].empty_label = "Selecione a unidade..."
        self.fields['servidor'].empty_label = "Selecione o servidor..."
        self.fields['calibre'].empty_label = "Selecione o calibre..."
        self.fields['tipo_arma'].empty_label = "Selecione o tipo..."
        self.fields['marca'].empty_label = "Selecione a marca..."
        self.fields['modelo'].empty_label = "Selecione o modelo..."

        # Adiciona classes para mobile
        for field in self.fields:
            if 'class' in self.fields[field].widget.attrs:
                self.fields[field].widget.attrs['class'] += ' sm:text-sm'

    def clean(self):
        cleaned_data = super().clean()
        servidor = cleaned_data.get('servidor')
        unidade = cleaned_data.get('unidade')

        if servidor and unidade:
            raise forms.ValidationError(
                "O armamento não pode estar associado a um servidor e uma unidade simultaneamente. "
                "Escolha apenas um ou deixe ambos em branco."
            )

        return cleaned_data


    # formularios municoes

class IncluirLoteForm(forms.ModelForm):
    class Meta:
        model = LoteMunicao
        fields = ['numero_lote', 'calibre', 'tipo', 'quantidade_inicial', 'data_validade', 'observacoes']
        widgets = {
            'numero_lote': forms.TextInput(attrs={'class': 'form-control'}),
            'calibre': forms.Select(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'quantidade_inicial': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'data_validade': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
        labels = {
            'quantidade_inicial': 'Quantidade Recebida',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("🔧 Formulário Iniciado:", self.data)  # Verifica dados recebidos

    def clean(self):
        cleaned_data = super().clean()
        print("🧼 Dados limpos:", cleaned_data)  # Verifica dados após validação
        return cleaned_data

    def clean_data_validade(self):
        data = self.cleaned_data.get('data_validade')
        print("📅 Validando data:", data)
        if data and data < timezone.now().date():
            raise ValidationError("Data de validade não pode ser no passado")
        return data

    def clean_numero_lote(self):
        numero = self.cleaned_data.get('numero_lote')
        print("🔢 Validando número do lote:", numero)
        if numero and LoteMunicao.objects.filter(numero_lote=numero).exists():
            raise ValidationError("Já existe um lote com este número")
        return numero




class MovimentarMunicaoForm(forms.ModelForm):
    destino_type = forms.ChoiceField(
        choices=[('unidade', 'Unidade'), ('servidor', 'Servidor')],
        widget=forms.RadioSelect,
        initial='unidade',
        label="Tipo de Destino"
    )

    class Meta:
        model = MovimentacaoMunicao
        fields = ['tipo', 'lote', 'quantidade', 'unidade_origem', 'unidade_destino', 'servidor_destino', 'documento_referencia']
        widgets = {
            'documento_referencia': forms.TextInput(attrs={
                'placeholder': 'Nº documento ou justificativa',
                'class': 'form-control'
            }),
            'quantidade': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'unidade_destino': forms.Select(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'servidor_destino': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'tipo': 'Tipo de Transferência',
            'unidade_destino': 'Unidade Destino',
            'servidor_destino': 'Servidor Destino',
            'unidade_origem': 'Unidade Origem',
            'documento_referencia': 'Documento/Justificativa'
        }

    def __init__(self, *args, **kwargs):
        unidade_origem_id = kwargs.pop('unidade_origem_id', None)
        lote_id = kwargs.pop('lote_id', None)
        super().__init__(*args, **kwargs)

        # Configura campos com base nos parâmetros
        if unidade_origem_id:
            self.fields['unidade_origem'].initial = unidade_origem_id
            self.fields['unidade_origem'].widget = forms.HiddenInput()

            # Filtra lotes disponíveis na unidade de origem
            self.fields['lote'].queryset = LoteMunicao.objects.filter(
                estoques__unidade=unidade_origem_id,
                estoques__quantidade__gt=0
            ).distinct()

            # Filtra servidores da unidade de origem
            self.fields['servidor_destino'].queryset = Servidor.objects.filter(
                unidade=unidade_origem_id
            )

        if lote_id:
            self.fields['lote'].initial = lote_id
            self.fields['lote'].widget = forms.HiddenInput()



        # Oculta campos não relevantes inicialmente

        self.fields['servidor_destino'].required = False

    def clean(self):
        cleaned_data = super().clean()
        destino_type = cleaned_data.get('destino_type')

        if destino_type == 'unidade':
            if cleaned_data.get('unidade_origem') == cleaned_data.get('unidade_destino'):
                raise ValidationError({
                    'unidade_destino': 'A unidade destino deve ser diferente da origem'
                })
            cleaned_data['servidor_destino'] = None
            self.fields['unidade_destino'].required = True
        else:
            if not cleaned_data.get('servidor_destino'):
                raise ValidationError({
                    'servidor_destino': 'Informe o servidor destino'
                })
            cleaned_data['unidade_destino'] = None
            cleaned_data['tipo'] = 'T'  # Distribuição para servidor
            self.fields['servidor_destino'].required = True

        return cleaned_data


class BaixarMunicaoForm(forms.ModelForm):
    destino_type = forms.ChoiceField(
        choices=[('unidade', 'Unidade'), ('servidor', 'Servidor')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Destino"
    )
    unidade = forms.ModelChoiceField(
        queryset=Unidade.objects.all(),
        required=False,
        label="Unidade",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    servidor = forms.ModelChoiceField(
        queryset=Servidor.objects.all(),
        required=False,
        label="Servidor",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = BaixaMunicao
        fields = ['destino_type', 'unidade', 'servidor', 'lote', 'quantidade', 'motivo', 'documento_referencia']
        widgets = {
            'lote': forms.Select(attrs={'class': 'form-select'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'documento_referencia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nº documento (opcional)'})
        }



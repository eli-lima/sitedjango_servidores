from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
# Importa as configurações do Django


# Create your models here.


class Calibre(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome

    class Meta:
        ordering = ['nome']  # Ordena por nome em ordem alfabética


class TipoArma(models.Model):
    nome = models.CharField(max_length=100)


    def __str__(self):
        return self.nome

    class Meta:
        ordering = ['nome']  # Ordena por nome em ordem alfabética


class Marca(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome

    class Meta:
        ordering = ['nome']  # Ordena por nome em ordem alfabética


class Modelo(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome

    class Meta:
        ordering = ['nome']  # Ordena por nome em ordem alfabética


STATUS = [
        (True, 'ATIVO'),
        (False, 'INATIVO'),
    ]


class Armamento(models.Model):
    tipo_arma = models.ForeignKey(TipoArma, on_delete=models.CASCADE)
    calibre = models.ForeignKey(Calibre, on_delete=models.CASCADE)
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE)
    modelo = models.ForeignKey(Modelo, on_delete=models.CASCADE)
    numero_serie = models.CharField(max_length=100)
    servidor = models.ForeignKey('servidor.Servidor', on_delete=models.CASCADE, null=True, blank=True)
    unidade = models.ForeignKey('seappb.Unidade', on_delete=models.CASCADE, null=True, blank=True)
    usuario = models.ForeignKey('seappb.Usuario', on_delete=models.CASCADE)
    observacao = models.TextField(null=True, blank=True)
    data_inclusao = models.DateTimeField(default=timezone.now)
    status = models.BooleanField(max_length=50, choices=STATUS, default='ATIVO')

    def __str__(self):
        return f"{self.tipo_arma} - {self.modelo}"

    class Meta:
        ordering = ['modelo']  # Ordena por nome em ordem alfabética


class ArmamentoHistory(models.Model):
    armamento = models.ForeignKey(Armamento, on_delete=models.CASCADE)
    campo_alterado = models.CharField(max_length=100)
    valor_antigo = models.TextField(null=True, blank=True)
    valor_novo = models.TextField(null=True, blank=True)
    data_alteracao = models.DateTimeField(auto_now_add=True)

    # Use settings.AUTH_USER_MODEL para referenciar o modelo de usuário
    usuario_responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)


class TermoAcautelamentoCounter(models.Model):
    year = models.IntegerField(unique=True)
    last_number = models.IntegerField(default=0)

    @classmethod
    def get_next_number(cls):
        current_year = timezone.now().year
        counter, created = cls.objects.get_or_create(
            year=current_year,
            defaults={'last_number': 0}
        )
        counter.last_number += 1
        counter.save()
        return f"{counter.last_number:02d}/{current_year}"

    class Meta:
        verbose_name = "Contador de Termos de Acautelamento"
        verbose_name_plural = "Contadores de Termos de Acautelamento"




#tabela municoes





class TipoMunicao(models.Model):
    """Tipos de munição (FMJ, HP, Blindada, etc.)"""
    nome = models.CharField(max_length=50, unique=True)
    descricao = models.TextField(blank=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Tipo de Munição"
        verbose_name_plural = "Tipos de Munição"
        ordering = ['nome']


class LoteMunicao(models.Model):
    """Informações completas sobre cada lote recebido"""
    numero_lote = models.CharField(max_length=50, unique=True, verbose_name="Número do Lote")
    calibre = models.ForeignKey(Calibre, on_delete=models.PROTECT)
    tipo = models.ForeignKey(TipoMunicao, on_delete=models.PROTECT)
    quantidade_inicial = models.PositiveIntegerField(verbose_name="Quantidade Recebida")
    data_validade = models.DateField()
    data_recebimento = models.DateField(default=timezone.now, verbose_name="Data de Recebimento")
    observacoes = models.TextField(blank=True)

    @property
    def saldo_atual(self):
        """Calcula o saldo atual baseado nas movimentações"""

        entradas = self.movimentacoes.filter(tipo='E').aggregate(Sum('quantidade'))['quantidade__sum'] or 0
        saidas = self.movimentacoes.filter(tipo__in=['S', 'T', 'B']).aggregate(Sum('quantidade'))[
                     'quantidade__sum'] or 0
        return entradas - saidas

    def clean(self):
        """Validações adicionais"""
        if self.data_validade < timezone.now().date():
            raise ValidationError("Data de validade não pode ser no passado")

    def __str__(self):
        return f"{self.numero_lote} - {self.calibre} {self.tipo}"

    class Meta:
        verbose_name = "Lote de Munição"
        verbose_name_plural = "Lotes de Munição"
        ordering = ['-data_recebimento']


class MovimentacaoMunicao(models.Model):
    """Controla TODAS as movimentações (entradas, saídas, transferências e baixas)"""
    TIPO_CHOICES = [

        ('T', 'Transferência'),
        ('E', 'Entrada'),



    ]

    lote = models.ForeignKey(LoteMunicao, on_delete=models.PROTECT, related_name='movimentacoes')
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES)
    quantidade = models.PositiveIntegerField()

    # Para transferências, saídas e baixas
    unidade_origem = models.ForeignKey(
        'seappb.Unidade',
        on_delete=models.PROTECT,
        related_name='movimentacoes_saida',
        null=True,
        blank=True
    )

    # Para transferências e entradas
    unidade_destino = models.ForeignKey(
        'seappb.Unidade',
        on_delete=models.PROTECT,
        related_name='movimentacoes_entrada',
        null=True,
        blank=True
    )

    # Para distribuição a servidores
    servidor_destino = models.ForeignKey(
        'servidor.Servidor',
        on_delete=models.PROTECT,
        related_name='municoes_recebidas',
        null=True,
        blank=True,
        verbose_name="Servidor Destino"
    )


    data_registro = models.DateTimeField(auto_now_add=True)
    responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    documento_referencia = models.CharField(max_length=100, blank=True, verbose_name="Documento de Referência")

    def clean(self):
        """Validações complexas"""
        errors = {}

        # Validações por tipo de movimentação
        if self.tipo == 'T':  # Transferência entre unidades
            if not self.unidade_destino:
                errors['unidade_destino'] = "Para transferência, informe a unidade destino"
            if not self.unidade_origem:
                errors['unidade_origem'] = "Para transferência, informe a unidade origem"
            if self.unidade_origem == self.unidade_destino:
                errors['unidade_destino'] = "Unidade destino deve ser diferente da origem"

        elif self.tipo == 'D':  # Distribuição para servidor
            if not self.servidor_destino:
                errors['servidor_destino'] = "Para distribuição, informe o servidor destino"
            if not self.unidade_origem:
                errors['unidade_origem'] = "Informe a unidade de origem"

        elif self.tipo in ['S', 'B']:  # Saída ou Baixa
            if not self.unidade_origem:
                errors['unidade_origem'] = "Informe a unidade de origem"

        elif self.tipo == 'E':  # Entrada
            if not self.unidade_destino:
                errors['unidade_destino'] = "Para entrada, informe a unidade destino"

        # Validação de quantidade
        if self.quantidade <= 0:
            errors['quantidade'] = "Quantidade deve ser maior que zero"

        # Verifica estoque para saídas/transferências/baixas/distribuições
        if self.tipo in ['S', 'T', 'B', 'D'] and self.unidade_origem:
            estoque = EstoqueMunicao.objects.filter(
                lote=self.lote,
                unidade=self.unidade_origem
            ).first()
            if estoque and estoque.quantidade < self.quantidade:
                errors['quantidade'] = f"Quantidade indisponível. Disponível: {estoque.quantidade}"

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Atualiza os estoques automaticamente"""
        self.full_clean()  # Executa as validações

        with transaction.atomic():
            is_new = self._state.adding

            if is_new:
                # Para saídas/transferências/baixas/distribuições
                if self.tipo in ['S', 'T', 'B', 'D']:
                    estoque_origem = EstoqueMunicao.objects.get(
                        lote=self.lote,
                        unidade=self.unidade_origem
                    )
                    estoque_origem.quantidade -= self.quantidade
                    estoque_origem.save()

                # Para entradas/transferências
                if self.tipo in ['E', 'T']:
                    estoque_destino, created = EstoqueMunicao.objects.get_or_create(
                        lote=self.lote,
                        unidade=self.unidade_destino,
                        defaults={'quantidade': self.quantidade}
                    )
                    if not created:
                        estoque_destino.quantidade += self.quantidade
                        estoque_destino.save()

            super().save(*args, **kwargs)

    def __str__(self):
        destino = self.unidade_destino or self.servidor_destino or "Baixa"
        return f"{self.get_tipo_display()} - {self.lote} para {destino} ({self.quantidade})"

    class Meta:
        verbose_name = "Movimentação de Munição"
        verbose_name_plural = "Movimentações de Munição"
        ordering = ['-data_registro']


class EstoqueMunicao(models.Model):
    """Visão consolidada do estoque por unidade"""
    lote = models.ForeignKey(LoteMunicao, on_delete=models.CASCADE)
    unidade = models.ForeignKey('seappb.Unidade', on_delete=models.CASCADE, null=True, blank=True)
    servidor = models.ForeignKey('servidor.Servidor', on_delete=models.CASCADE, null=True, blank=True)
    quantidade = models.PositiveIntegerField(default=0)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('lote', 'unidade')
        verbose_name = "Estoque de Munição"
        verbose_name_plural = "Estoques de Munição"

    def __str__(self):
        return f"{self.lote} - {self.unidade} ({self.quantidade})"


class BaixaMunicao(models.Model):
    """Registro de baixa de munições com atualização de estoque"""
    lote = models.ForeignKey(LoteMunicao, on_delete=models.PROTECT)
    quantidade = models.PositiveIntegerField()

    # Pode ser para unidade OU servidor (nunca ambos)
    unidade = models.ForeignKey(
        'seappb.Unidade',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    servidor = models.ForeignKey(
        'servidor.Servidor',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    motivo = models.TextField(verbose_name="Motivo da Baixa")
    documento_referencia = models.CharField(max_length=50, blank=True)
    data_registro = models.DateTimeField(auto_now_add=True)
    responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    def clean(self):
        """Validação para garantir que é unidade OU servidor, nunca ambos"""
        errors = {}

        if not self.unidade and not self.servidor:
            errors['unidade'] = "Informe a unidade ou servidor"
            errors['servidor'] = "Informe a unidade ou servidor"
        elif self.unidade and self.servidor:
            errors['unidade'] = "Selecione apenas unidade ou servidor"
            errors['servidor'] = "Selecione apenas unidade ou servidor"

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Atualiza o estoque ao registrar a baixa"""
        self.full_clean()

        with transaction.atomic():
            # Verifica se é novo registro
            is_new = self._state.adding

            if is_new:
                # Diminui do estoque da unidade ou servidor
                try:
                    if self.unidade:
                        estoque = EstoqueMunicao.objects.get(
                            lote=self.lote,
                            unidade=self.unidade
                        )
                    else:
                        estoque = EstoqueMunicao.objects.get(
                            lote=self.lote,
                            servidor=self.servidor
                        )
                except EstoqueMunicao.DoesNotExist:
                    raise ValidationError("Não há estoque disponível para este lote na unidade ou servidor informado.")

                if estoque.quantidade < self.quantidade:
                    raise ValidationError("Quantidade indisponível para baixa")

                estoque.quantidade -= self.quantidade
                estoque.save()

            super().save(*args, **kwargs)

    def __str__(self):
        destino = self.unidade if self.unidade else self.servidor
        return f"Baixa de {self.quantidade} - Lote {self.lote} - {destino}"

    class Meta:
        verbose_name = "Baixa de Munição"
        verbose_name_plural = "Baixas de Munição"
        ordering = ['-data_registro']

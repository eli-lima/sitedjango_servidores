from django.contrib import admin
from .models import (
    Calibre, TipoArma, Marca, Modelo, Armamento, ArmamentoHistory,
    TipoMunicao, LoteMunicao, MovimentacaoMunicao, EstoqueMunicao, BaixaMunicao
)


@admin.register(Armamento)
class ArmamentoAdmin(admin.ModelAdmin):
    list_display = (
        'tipo_arma', 'calibre', 'marca', 'modelo', 'numero_serie',
        'servidor', 'unidade', 'usuario', 'status', 'data_inclusao'
    )
    search_fields = (
        'numero_serie',
        'servidor__nome', 'servidor__matricula',
        'unidade__nome',
        'usuario__username',
    )
    list_filter = ('tipo_arma', 'calibre', 'marca', 'modelo', 'status')
    ordering = ('-data_inclusao',)


@admin.register(ArmamentoHistory)
class ArmamentoHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'armamento', 'campo_alterado', 'valor_antigo',
        'valor_novo', 'data_alteracao', 'usuario_responsavel'
    )
    search_fields = (
        'armamento__numero_serie',
        'campo_alterado',
        'usuario_responsavel__username'
    )
    list_filter = ('campo_alterado', 'data_alteracao')


# Modelos básicos (comuns a armas e munições)
@admin.register(Calibre)
class CalibreAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)
    ordering = ('nome',)


@admin.register(TipoArma)
class TipoArmaAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)
    ordering = ('nome',)


@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)
    ordering = ('nome',)


@admin.register(Modelo)
class ModeloAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)
    ordering = ('nome',)


# Modelos específicos de munição
@admin.register(TipoMunicao)
class TipoMunicaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome', 'descricao')
    ordering = ('nome',)


@admin.register(LoteMunicao)
class LoteMunicaoAdmin(admin.ModelAdmin):
    list_display = ('numero_lote', 'calibre', 'tipo', 'quantidade_inicial',
                    'saldo_atual', 'data_validade', 'data_recebimento')
    search_fields = ('numero_lote', 'calibre__nome', 'tipo__nome')
    list_filter = ('calibre', 'tipo', 'data_recebimento')
    ordering = ('-data_recebimento',)
    readonly_fields = ('saldo_atual',)
    fieldsets = (
        (None, {
            'fields': ('numero_lote', 'calibre', 'tipo')
        }),
        ('Quantidades', {
            'fields': ('quantidade_inicial', 'saldo_atual')
        }),
        ('Datas', {
            'fields': ('data_validade', 'data_recebimento')
        }),
        ('Outros', {
            'fields': ('observacoes',)
        }),
    )


@admin.register(MovimentacaoMunicao)
class MovimentacaoMunicaoAdmin(admin.ModelAdmin):
    list_display = ('lote', 'get_tipo_display', 'quantidade',
                    'unidade_origem', 'unidade_destino',
                    'data_registro', 'responsavel')
    search_fields = ('lote__numero_lote', 'documento_referencia',
                     'unidade_origem__nome', 'unidade_destino__nome',
                     'responsavel__username')
    list_filter = ('tipo', 'data_registro', 'lote__calibre')
    ordering = ('-data_registro',)
    raw_id_fields = ('lote', 'unidade_origem', 'unidade_destino', 'responsavel')

    def get_tipo_display(self, obj):
        return obj.get_tipo_display()

    get_tipo_display.short_description = 'Tipo'


@admin.register(EstoqueMunicao)
class EstoqueMunicaoAdmin(admin.ModelAdmin):
    list_display = ('lote', 'unidade', 'servidor', 'quantidade', 'data_atualizacao')
    search_fields = ('lote__numero_lote', 'unidade__nome', 'servidor')
    list_filter = ('unidade', 'servidor', 'lote__calibre')
    ordering = ('unidade', 'servidor', 'lote__numero_lote')
    readonly_fields = ('data_atualizacao',)


@admin.register(BaixaMunicao)
class BaixaMunicaoAdmin(admin.ModelAdmin):
    list_display = ('lote', 'quantidade', 'unidade', 'servidor', 'responsavel', 'data_registro')
    search_fields = ('lote__numero_lote', 'unidade__nome', 'servidor__nome', 'responsavel__username')
    list_filter = ('unidade', 'servidor', 'lote__calibre', 'responsavel')
    ordering = ('-data_registro',)
    readonly_fields = ('data_registro', 'responsavel')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('lote', 'unidade', 'servidor', 'responsavel')


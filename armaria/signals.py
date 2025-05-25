from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Armamento, ArmamentoHistory


@receiver(pre_save, sender=Armamento)
def registrar_alteracoes_servidor(sender, instance, **kwargs):
    try:
        armamento_antigo = Armamento.objects.get(pk=instance.pk)
    except Armamento.DoesNotExist:
        # O registro é novo, portanto não há alterações a serem registradas
        return

    campos_para_monitorar = ['armamento', 'unidade', 'status', 'usuario']

    for campo in campos_para_monitorar:
        valor_antigo = getattr(armamento_antigo, campo)
        valor_novo = getattr(instance, campo)

        # Converte valores None para strings vazias
        valor_antigo = valor_antigo if valor_antigo is not None else ""
        valor_novo = valor_novo if valor_novo is not None else ""

        if valor_antigo != valor_novo:  # Se o valor foi alterado
            ArmamentoHistory.objects.create(
                armamento=instance,
                campo_alterado=campo,
                valor_antigo=valor_antigo,
                valor_novo=valor_novo,
                usuario_responsavel=instance.usuario_responsavel if hasattr(instance, 'usuario_responsavel') else None
            )
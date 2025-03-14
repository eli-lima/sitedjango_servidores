from django.db.models import Sum
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import LimiteAjudaCusto, CotaAjudaCusto

@receiver([post_save, post_delete], sender=LimiteAjudaCusto)
def atualizar_carga_horaria_disponivel(sender, instance, **kwargs):
    # Encontra a CotaAjudaCusto associada à unidade do LimiteAjudaCusto
    cota = CotaAjudaCusto.objects.filter(unidade=instance.unidade).first()
    if cota:
        # Recalcula as horas distribuídas
        distribuidas = LimiteAjudaCusto.objects.filter(unidade=instance.unidade).aggregate(
            total_distribuido=Sum('limite_horas')
        )['total_distribuido'] or 0
        # Atualiza a carga horária disponível
        cota.carga_horaria_disponivel = cota.carga_horaria_total - distribuidas
        cota.save()

@receiver(post_delete, sender=CotaAjudaCusto)
def atualizar_carga_horaria_apos_exclusao(sender, instance, **kwargs):
    # Encontra a CotaAjudaCusto associada à unidade (se houver)
    cota = CotaAjudaCusto.objects.filter(unidade=instance.unidade).first()
    if cota:
        # Recalcula as horas distribuídas
        distribuidas = LimiteAjudaCusto.objects.filter(unidade=instance.unidade).aggregate(
            total_distribuido=Sum('limite_horas')
        )['total_distribuido'] or 0
        # Atualiza a carga horária disponível
        cota.carga_horaria_disponivel = cota.carga_horaria_total - distribuidas
        cota.save()
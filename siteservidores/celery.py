from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Define as configurações padrão do Django para o ambiente 'celery'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'siteservidores.settings')

app = Celery('siteservidores')

# Usa as configurações do Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Carrega automaticamente as tarefas dos apps instalados
app.autodiscover_tasks()

# Adicione configurações adicionais para otimização
app.conf.update(
    worker_max_tasks_per_child=100,  # Reinicia o worker após 100 tarefas para liberar memória
    worker_prefetch_multiplier=1,  # Evita que os workers fiquem com muitas tarefas ao mesmo tempo
    broker_connection_retry_on_startup=True,  # Garante que a reconexão seja feita corretamente
)

# Definição do agendamento para exclusão de PDFs antigos
app.conf.beat_schedule = {
    'delete-old-pdfs-every-two-weeks': {
        'task': 'servidor.tasks.delete_old_pdfs',  # Certifique-se de usar o nome correto do app
        'schedule': crontab(minute=0, hour=0, day_of_week='sunday', day_of_month='*/14'),  # Executa a cada 14 dias
    },
}

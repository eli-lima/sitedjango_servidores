from django.apps import AppConfig


class ServidorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'servidor'

    def ready(self):
        import servidor.signals  # Certifique-se de que o signal está sendo carregado
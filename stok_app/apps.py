from django.apps import AppConfig

class StokAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stok_app'

    def ready(self):
        import stok_app.signals  # Signals'ı yükle

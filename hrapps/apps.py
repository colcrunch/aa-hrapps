from django.apps import AppConfig
from django.db.models.signals import post_save

from . import __version__

class HrappsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hrapps'
    verbose_name = f"HRApps v{__version__}"

    def ready(self):
        from . import signals
        from .models import HRAppDiscordSettings

        post_save.connect(signals.announce_update, sender=HRAppDiscordSettings)

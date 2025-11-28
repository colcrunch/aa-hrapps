from django.apps import AppConfig

from . import __version__

class HrappsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hrapps'
    verbose_name = f"HRApps v{__version__}"

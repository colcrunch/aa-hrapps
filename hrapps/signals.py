import json

from django.db.models.signals import post_save
from django.dispatch import receiver
from allianceauth.utils.cache import get_redis_client
from allianceauth.services.hooks import get_extension_logger

from .models import HRAppDiscordSettings

logger = get_extension_logger(__name__)


def announce_update(sender, **kwargs):
    logger.debug("Received settings update")
    redis_client = get_redis_client()
    message = {"action": "settings_updated"}

    redis_client.publish("hrapp_discord_settings", json.dumps(message))
    logger.debug("Published settings update message")
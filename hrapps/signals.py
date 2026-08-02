import json

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.conf import settings
from allianceauth.utils.cache import get_redis_client
from allianceauth.services.hooks import get_extension_logger
from allianceauth.notifications.models import Notification

from .models import FormResponse, StatusChoices, ResponseComment

logger = get_extension_logger(__name__)


def announce_update(sender, **kwargs):
    logger.debug("Received settings update")
    redis_client = get_redis_client()
    message = {"action": "settings_updated"}

    redis_client.publish("hrapp_discord_settings", json.dumps(message))
    logger.debug("Published settings update message")

def get_notification_users(corp):
    all_resp_users = get_user_model().objects.with_perm("hrapps.view_all_responses", backend="django.contrib.auth.backends.ModelBackend")
    all_corp_users = (get_user_model()
                      .objects
                      .with_perm("hrapps.view_corp_responses", backend="django.contrib.auth.backends.ModelBackend")
                      .filter(profile__main_character__corporation_id=corp.corporation_id))

    users = set(list(all_corp_users) + list(all_resp_users))

    logger.debug(users)
    return users

@receiver(post_save, sender=FormResponse)
def notify_recruiters(sender, instance, created, **kwargs):
    corp = instance.form.corporation
    users = get_notification_users(corp)
    application_user = instance.user.profile.main_character.character_name
    if created:
        logger.debug("Created!")
        for user in users:
            Notification.objects.notify_user(
                user=user,
                title=f"New Application to {corp.corporation_name}",
                message=f"{application_user} has submitted an application to join {corp.corporation_name}.",
                level=Notification.Level.INFO
            )
    return

if "aadiscordbot" in settings.INSTALLED_APPS:
    @receiver(post_save, sender=FormResponse)
    def announce_new_app(sender, instance, created, **kwargs):
        if created:
            logger.debug("New application; Publishing to Redis")
            client = get_redis_client()
            message = {"action": "new application", "app_pk": instance.pk}

            client.publish("hrapp_application_notifications", json.dumps(message))
            logger.debug("Published new application notification")
        return

    @receiver(post_save, sender=ResponseComment)
    def announce_comment(sender, instance, created, **kwargs):
        if created:
            logger.debug("New comment; Publishing to Redis")
            client = get_redis_client()
            message = {"action": "new comment", "comment_pk": instance.pk}

            client.publish("hrapp_comment_notifications", json.dumps(message))
            logger.debug("Published new comment notification")
        return

@receiver(pre_save, sender=FormResponse)
def append_previous_state(sender, instance, **kwargs):
    try:
        before = FormResponse.objects.get(pk=instance.pk)

        prev_state = dict()
        prev_state["status"] = before.status
        prev_state["recruiter"] = before.recruiter
        prev_state["reviewer"] = before.reviewer

        instance._prev_state = prev_state
    except FormResponse.DoesNotExist:
        pass
    logger.debug("PREV HAPPENED")

@receiver(post_save, sender=FormResponse)
def notify_user(sender, instance, created, **kwargs):
    if created:
        msg = f"You have applied to join {instance.form.corporation.corporation_name}."
        Notification.objects.notify_user(
            user=instance.user,
            title="Application Submitted",
            message=msg,
            level=Notification.Level.INFO
        )
        return
    msg = ""
    title = ""
    prev_state = instance._prev_state
    level = Notification.Level.INFO

    if instance.recruiter != prev_state["recruiter"]:
        title = "Application claimed by recruiter"
        msg = (f"{instance.recruiter.profile.main_character.character_name} "
               f"has claimed your application to join {instance.form.corporation.corporation_name}.")
    if instance.reviewer != prev_state["reviewer"]:
        title = "Application claimed by reviewer"
        msg = (f"{instance.reviewer.profile.main_character.character_name} "
               f"has claimed your application to join {instance.form.corporation.corporation_name}.")
    if instance.status == StatusChoices.REJECTED or instance.status == StatusChoices.APPROVED:
        title = f"Application {instance.status}"
        msg = f"Your application to join {instance.form.corporation.corporation_name} has been {instance.status}."
        level = Notification.Level.DANGER if instance.status == StatusChoices.REJECTED else Notification.Level.SUCCESS
    elif instance.status != prev_state["status"]:
        title = "Application status updated"
        msg = (f"The status of your application to join {instance.form.corporation.corporation_name} has changed.\n"
               f"Previous Status: {instance._prev_state['status']}\n"
               f"New Status: {instance.status}")

    Notification.objects.notify_user(
        user=instance.user,
        title=title,
        message=msg,
        level=level
    )


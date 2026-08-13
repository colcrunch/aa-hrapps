import allianceauth.authentication.models
from django.db import models
from django.db.models import Q
from allianceauth.eveonline.models import EveCorporationInfo
from django.contrib.auth.models import User
from solo.models import SingletonModel

# Create your models here.
class HRAppPerms(models.Model):
    class Meta:
        managed = False
        default_permissions = (())
        permissions = (
            ("access_hrapps", "Can access hrapps."),
            ("access_hradmin", "Can access the admin frontend."),
            ("manage_hrapps", "Full management access."),
        )


class HRAppDiscordSettings(SingletonModel):
    # Welcome message settings
    enable_welcome_messages = models.BooleanField(default=False)
    welcome_channel = models.BigIntegerField(null=True, blank=True)
    welcome_message = models.TextField(null=True, blank=True)
    ignored_states = models.ManyToManyField(allianceauth.authentication.models.State, blank=True)

    # Recruitment thread settings
    use_recruitment_threads = models.BooleanField(default=False)
    recruitment_thread_channel = models.BigIntegerField(null=True, blank=True)
    recruiter_role = models.BigIntegerField(null=True, blank=True)
    recruit_role = models.BigIntegerField(null=True, blank=True)

    # Notification Settings
    enable_application_notifications = models.BooleanField(default=False)
    application_notification_channel = models.BigIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "HRApp Discord Settings"
        default_permissions = (())

        constraints = [
            models.CheckConstraint(
                check=Q(use_recruitment_threads=False) | Q(recruitment_thread_channel__isnull=False),
                name="recruitment_thread_channel_required_if_threads_enabled"),
            models.CheckConstraint(
                check=Q(enable_welcome_messages=False) | Q(welcome_channel__isnull=False),
                name="welcome_channel_required_if_welcome_messages_enabled")
        ]



class Form(models.Model):
    corporation = models.ForeignKey(EveCorporationInfo, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=100)
    fields = models.JSONField()
    description = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.active:
            Form.objects.filter(corporation=self.corporation, active=True).update(active=False)
        super().save(*args, **kwargs)

    class Meta:
        default_permissions = (())
        permissions = (
            ("manage_all_forms", "Can manage forms."),
            ("create_forms", "Can create forms."),
            ("manage_corp_forms", "Can manage corp forms."),
        )
        constraints = [
            models.UniqueConstraint(
                fields=["corporation", "active"],
                condition=models.Q(active=True),
                name="only_one_active_form_per_corp"
            ),
            models.UniqueConstraint(fields=["corporation", "name"], name="unique_form_name_per_corp")
        ]


class StatusChoices(models.TextChoices):
    PENDING = "pending", "Pending"
    UNDER_REVIEW = "under_review", "Under Review"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    WITHDRAWN = "withdrawn", "Withdrawn"


class FormResponse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    form = models.ForeignKey(Form, on_delete=models.DO_NOTHING, related_name="responses")
    created = models.DateTimeField(auto_now_add=True)
    response = models.JSONField()
    recruiter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="recruited_responses")
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="reviewed_responses")
    status = models.CharField(max_length=15, choices=StatusChoices.choices, default=StatusChoices.PENDING)

    @property
    def status_color_class(self):
        colors = {
            "pending": "primary",
            "under_review": "warning",
            "approved": "success",
            "rejected": "danger",
            "withdrawn": "secondary"
        }
        return colors[self.status]

    @property
    def status_label(self):
        return StatusChoices(self.status).label

    @property
    def is_closed(self):
        return self.status in ("approved", "rejected", "withdrawn")

    class Meta:
        default_permissions = (())
        permissions = (
            ("view_all_responses", "Can view responses."),
            ("create_response", "Can create responses."),
            ("view_corp_responses", "Can view corp responses."),
            ("claim_recruiter", "Can claim a response as a recruiter."),
            ("claim_reviewer", "Can claim a response as a reviewer."),
            ("modify_status", "Can change the status of a response.")
        )


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content = models.TextField(null=False, blank=False)
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, related_name='replies')
    created = models.DateTimeField(auto_now_add=True, null=False)

    class Meta:
        default_permissions = (())

class ResponseComment(Comment):
    response = models.ForeignKey(FormResponse, on_delete=models.CASCADE, related_name="comments")
    # Private comments and their replies should be hidden from the respondent even if they have the permissions
    # to view/create comments. (Except where user has manage_hrapps perm)
    private = models.BooleanField(default=False)


    class Meta:
        default_permissions = (())
        permissions = (
            ("create_comment", "Can comment on form responses."),       # Can create AND view
            ("view_comment", "Can view comments on form responses."),   # Can view but NOT create
        )


class Attachment(models.Model):
    response = models.ForeignKey(FormResponse, on_delete=models.CASCADE, related_name="attachments")
    file = models.ImageField(upload_to="hrapps/attachments/")
    question_id = models.IntegerField(null=True, blank=True)

    class Meta:
        default_permissions = (())

from django.db import models
from allianceauth.eveonline.models import EveCorporationInfo
from django.contrib.auth.models import User

# Create your models here.
class HRAppPerms(models.Model):
    class Meta:
        managed = False
        default_permissions = (())
        permissions = (
            ("access_hrapps", "Can access hrapps."),
            ("manage_hrapps", "Full management access."),
        )


class Form(models.Model):
    corporation = models.ForeignKey(EveCorporationInfo, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=100)
    fields = models.JSONField()
    description = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        default_permissions = (())
        permissions = (
            ("manage_all_forms", "Can manage forms."),
            ("create_forms", "Can create forms."),
            ("manage_corp_forms", "Can manage corp forms."),
        )

class FormResponse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    form = models.ForeignKey(Form, on_delete=models.DO_NOTHING, related_name="responses")
    response = models.JSONField()

    class Meta:
        default_permissions = (())
        permissions = (
            ("view_all_responses", "Can view responses."),
            ("create_response", "Can create responses."),
            ("view_corp_responses", "Can view corp responses."),
        )

class ResponseComment(models.Model):
    response = models.ForeignKey(FormResponse, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content = models.TextField(null=False, blank=False)
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, related_name='replies')
    # Private comments and their replies should be hidden from the respondent even if they have the permissions
    # to view/create comments. (Except where user has manage_hrapps perm)
    private = models.BooleanField(default=False)

    class Meta:
        default_permissions = (())
        permissions = (
            ("create_comment", "Can comment on form responses."),       # Can create AND view
            ("view_comment", "Can view comments on form responses."),   # Can view but NOT create
        )

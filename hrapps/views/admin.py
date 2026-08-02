import copy
import json

from allianceauth.authentication.decorators import permissions_required
from allianceauth.authentication.models import State
from django.http import HttpResponse
from django.contrib import messages
from django.shortcuts import render, redirect
from django.conf import settings

from allianceauth.services.hooks import get_extension_logger
from allianceauth.eveonline.models import EveCorporationInfo

from hrapps.models import Form, FormResponse, HRAppDiscordSettings
from . import Field, get_application_context, add_comment, add_reply

logger = get_extension_logger(__name__)


def get_or_create_corp(corporation_id):
    try:
        corp = EveCorporationInfo.objects.get(corporation_id=corporation_id)
    except EveCorporationInfo.DoesNotExist:
        EveCorporationInfo.objects.create_corporation(corporation_id)
        corp = EveCorporationInfo.objects.get(corporation_id=corporation_id)
    return corp


# Create your views here.
def dashboard(request):
    user_corp = request.user.profile.main_character.corporation_id
    if request.user.is_superuser or request.user.has_perm("hrapps.manage_hrapps"):
        active_apps = FormResponse.objects.filter(status__in=("pending", "under_review"))
    else:
        active_apps = FormResponse.objects\
            .filter(status__in=("pending", "under_review"), form__corporation__corporation_id=user_corp)

    discordbot_installed = "aadiscordbot" in settings.INSTALLED_APPS
    discord_settings = HRAppDiscordSettings.get_solo()
    states = State.objects.all()

    return render(
        request,
        "hrapps/admin/dashboard.html",
        {
            "active_apps": active_apps,
            "discordbot_installed": discordbot_installed,
            "discord_settings": discord_settings,
            "states": states,
        })


@permissions_required(("hrapps.manage_corp_forms", "hrapps.manage_all_forms", "hrapps.create_forms"))
def create_form(request):
    if request.method == "POST":
        body = request.body.decode("utf-8")
        logger.debug(body)
        body_json = json.loads(body)

        corp = get_or_create_corp(request.user.profile.main_character.corporation_id)
        form = Form(
            name=body_json["name"],
            description=body_json["description"],
            corporation=corp,
            active=body_json["active"],
            fields=body_json["questions"],
        )
        try:
            form.save()
        except Exception as e:
            logger.error(e)
            return HttpResponse(status=500)
        return HttpResponse(status=201)

    active_form_title = None
    corp_has_active_form = Form.objects.filter(corporation__corporation_id=request.user.profile.main_character.corporation_id, active=True).exists()
    if corp_has_active_form:
        active_form_title = Form.objects.get(corporation__corporation_id=request.user.profile.main_character.corporation_id, active=True).name

    return render(request, "hrapps/admin/builder.html",
                  {"action": "Create",
                   "has_active": corp_has_active_form,
                   "active_form_title": active_form_title})


def user_can_manage_form(request, corp: EveCorporationInfo):
    if request.user.has_perm("hrapps.manage_all_forms"):
        return True

    if request.user.profile.main_character.corporation_id != corp.corporation_id:
        return False

    return True


@permissions_required(("hrapps.manage_corp_forms", "hrapps.manage_all_forms"))
def edit_form(request, form_id):
    form = Form.objects.get(id=form_id)

    if not user_can_manage_form(request, Form.corporation):
        messages.error(request, "You do not have permission to manage this form.")
        sender = request.META.get("HTTP_REFERER", "/")
        return redirect(sender)

    if request.method == "POST":
        body = request.body.decode("utf-8")
        logger.debug(body)
        body_json = json.loads(body)

        form.name = body_json["name"]
        form.description = body_json["description"]
        form.active = body_json["active"]
        form.fields = body_json["questions"]
        try:
            form.save()
        except Exception as e:
            logger.error(e)
            return HttpResponse(status=500)
        return HttpResponse(status=200)
    fields = []

    for field in form.fields:
        field = Field(**field)
        fields.append(field)

    active_form_title = None
    corp_has_active_form = Form.objects.filter(
        corporation__corporation_id=request.user.profile.main_character.corporation_id, active=True).exists()
    if corp_has_active_form:
        active_form_title = Form.objects.get(
            corporation__corporation_id=request.user.profile.main_character.corporation_id, active=True).name

    fields = tuple(fields)
    return render(request, "hrapps/admin/builder.html",
                  {
                      "action": "Edit",
                      "form": form,
                      "fields": fields,
                      "has_active": corp_has_active_form,
                      "active_form_title": active_form_title,
                  })


@permissions_required(("hrapps.manage_corp_forms", "hrapps.manage_all_forms"))
def delete_form(request, form_id):
    sender = request.META.get("HTTP_REFERER", "/")

    try:
        form = Form.objects.get(id=form_id)

        if not user_can_manage_form(request, Form.corporation):
            messages.error(request, "You do not have permission to manage this form.")
            return redirect(sender)

        form.delete()

        messages.success(request, "Form deleted successfully.")
    except Exception as e:
        logger.error(e)
        messages.error(request, "Error deleting form.")
    return redirect(sender)


@permissions_required(("hrapps.manage_corp_forms", "hrapps.manage_all_forms", "hrapps.create_form"))
def view_form(request, form_id):
    form = Form.objects.get(id=form_id)

    if not user_can_manage_form(request, Form.corporation):
        messages.error(request, "You do not have permission to manage this form.")
        sender = request.META.get("HTTP_REFERER", "/")
        return redirect(sender)

    fields = []

    for field in form.fields:
        field = Field(**field)
        fields.append(field)

    fields = tuple(fields)
    return render(request, "hrapps/admin/form_viewer.html", {"action": "Edit", "form": form, "fields": fields})


@permissions_required(("hrapps.create_forms", "hrapps.manage_corp_forms"))
def copy_form(request, form_id):
    form = Form.objects.get(id=form_id)

    copied_form = copy.deepcopy(form)
    copied_form.pk = None
    copied_form.active = False
    if copied_form.corporation.corporation_id == request.user.profile.main_character.corporation_id:
        copied_form.name = f"{copied_form.name} (Copy)"
    else:
        copied_form.corporation__corporation_id = request.user.profile.main_character.corporation_id
    copied_form.save()

    return redirect("hradmin:edit_form", form_id=copied_form.pk)


@permissions_required(("hrapps.manage_corp_forms", "hrapps.manage_all_forms", "hrapps.create_form"))
def forms_library(request):
    forms = Form.objects.all()
    ctx = {"forms": forms}
    return render(request, "hrapps/admin/form_library.html", ctx)

def toggle_updates(response_id, question: str):
    response = FormResponse.objects.get(id=response_id)
    response_content = response.response
    idx = response_content["questions"].index(next((item for item in response_content["questions"] if item["question"] == question)))
    response_content["questions"][idx]["allowUpdates"] = not response_content["questions"][idx]["allowUpdates"]
    response.response = response_content
    response.save()

@permissions_required(("hrapps.view_all_responses", "hrapps.view_corp_responses"))
def view_response(request, response_id):
    ctx = get_application_context(request, response_id, True)

    if not request.user.has_perm("hrapps.view_all_responses"):
        # If you don't have view_all and are able to see then you must have view_corp.
        if not request.user.profile.main_character.corporation_id == ctx["application"].form.corporation.corporation_id:
            messages.error(request, "You do not have permission to view this response.")
            sender = request.META.get("HTTP_REFERER", "/")
            return redirect(sender)

    if ctx is None:
        messages.error(request, "The requested application could not be found.")
        return redirect("hradmin:dashboard")

    if request.method == "POST":
        question = request.POST.get("question")

        try:
            toggle_updates(response_id, question)
        except Exception as e:
            logger.error(e)
            messages.error(request, "An error occurred while toggling updates.")
            return redirect("hradmin:view_response", response_id)
        messages.success(request, "Updates toggled successfully.")
        return redirect("hradmin:view_response", response_id)

    return render(request, "hrapps/shared/view.html", ctx)

@permissions_required(("hrapps.modify_status",))
def approve_response(request, response_id):
    ctx = get_application_context(request, response_id, True)

    if ctx is None:
        # This should never happen
        # TODO: Send notification via auth to admins.
        messages.error(request, "An unexpected error occurred please report this to your IT team.")
        logger.critical(f"An unexpected error occurred when attempting to approve form response: {response_id}. "
                        f"Application context returned none. Please open an report this on the aa-hrapps github.")
        return redirect("hradmin:dashboard")

    application = ctx.get("application")
    application.status = "approved"
    application.save()

    # TODO: Notify applicant via auth notifications.
    messages.success(request, "Application approved successfully.")

    return redirect("hradmin:view_response", response_id)


@permissions_required(("hrapps.modify_status",))
def reject_response(request, response_id):
    ctx = get_application_context(request, response_id, True)

    if ctx is None:
        # This should never happen
        # TODO: Send notification via auth to admins.
        messages.error(request, "An unexpected error occurred please report this to your IT team.")
        logger.critical(f"An unexpected error occurred when attempting to reject form response: {response_id}. "
                        f"Application context returned none. Please open an report this on the aa-hrapps github.")
        return redirect("hradmin:dashboard")

    application = ctx.get("application")
    application.status = "rejected"
    application.save()

    # TODO: Notify applicant via auth notifications.
    messages.success(request, "Application successfully rejected.")

    return redirect("hradmin:view_response", response_id)


@permissions_required(("hrapps.manage_hrapps",))
def pend_response(request, response_id):
    ctx = get_application_context(request, response_id, True)

    if ctx is None:
        # This should never happen
        # TODO: Send notification via auth to admins.
        messages.error(request, "An unexpected error occurred please report this to your IT team.")
        logger.critical(f"An unexpected error occurred when attempting to pend form response: {response_id}. "
                        f"Application context returned none. Please open an report this on the aa-hrapps github.")
        return redirect("hradmin:dashboard")

    application = ctx.get("application")
    application.status = "pending"
    application.save()

    # TODO: Notify applicant via auth notifications.
    messages.info(request, "Application marked pending.")

    return redirect("hradmin:view_response", response_id)


@permissions_required(("hrapps.modify_status",))
def review_status_response(request, response_id):
    ctx = get_application_context(request, response_id, True)

    if ctx is None:
        # This should never happen
        # TODO: Send notification via auth to admins.
        messages.error(request, "An unexpected error occurred please report this to your IT team.")
        logger.critical(f"An unexpected error occurred when attempting change status of "
                        f"form response: {response_id} to Under Review. Application context returned none. "
                        f"Please open a report for this on the aa-hrapps github.")
        return redirect("hradmin:dashboard")

    application = ctx.get("application")
    application.status = "under_review"
    application.save()

    # TODO: Notify applicant via auth notifications.
    messages.warning(request, "Application marked Under Review.")

    return redirect("hradmin:view_response", response_id)


@permissions_required(("hrapps.claim_recruiter",))
def claim_recruiter(request, response_id):
    ctx = get_application_context(request, response_id, True)

    if ctx is None:
        # This should never happen.
        messages.error(request, "An unexpected error occurred please report this to your IT team.")
        logger.critical(f"An unexpected error occurred when attempting to claim recruiter form response: {response_id}."
                        f"Application context returned none. Please open a report for this on the aa-hrapps github.")
        return redirect("hradmin:dashboard")

    application = ctx.get("application")
    application.recruiter = request.user
    application.save()

    messages.success(request, "Claimed application as recruiter successfully.")
    return redirect("hradmin:view_response", response_id)


@permissions_required(("hrapps.claim_reviewer",))
def claim_reviewer(request, response_id):
    ctx = get_application_context(request, response_id, True)

    if ctx is None:
        # This should never happen.
        messages.error(request, "An unexpected error occurred please report this to your IT team.")
        logger.critical(f"An unexpected error occurred when attempting to claim reviewer form response: {response_id}."
                        f"Application context returned none. Please open a report for this on the aa-hrapps github.")

        return redirect("hradmin:dashboard")

    application = ctx.get("application")
    application.reviewer = request.user
    application.save()

    messages.success(request, "Claimed application as reviewer successfully.")
    return redirect("hradmin:view_response", response_id)


@permissions_required(("hrapps.create_comment",))
def create_comment(request, response_id):
    success = add_comment(request, response_id)
    if success:
        messages.success(request, "Comment added.")
    else:
        messages.error(request, "Unable to add comment.")
    return redirect("hradmin:view_response", response_id)


@permissions_required(("hrapps.create_comment",))
def create_reply(request, response_id, comment_id):
    success = add_reply(request, response_id, comment_id)
    if success:
        messages.success(request, "Reply added.")
    else:
        messages.error(request, "Unable to add reply.")
    return redirect("hradmin:view_response", response_id)


@permissions_required(("hrapps.manage_hrapps",))
def update_discord(request):
    if request.method != "POST":
        messages.error(request, "Invalid request.")
        logger.error(f"Invalid request to update discord settings, method: {request.method}. By {request.user}")
        return redirect("hradmin:dashboard")

    update_success = None
    keys = "".join(request.POST.keys())

    if "welcome" in keys:
        update_success = update_discord_welcome_settings(request)
    elif "recruitment" in keys:
        update_success = update_discord_recruitment_settings(request)
    elif "notification" in keys:
        update_success = update_discord_app_notification_settings(request)
    else:
        messages.error(request, "Invalid request.")
        logger.error(f"Invalid request to update discord settings, no keys found.")
        return redirect("hradmin:dashboard")

    if update_success is None or update_success is False:
        messages.error(request, "Failed to update discord settings.")
        logger.error(f"Failed to update discord settings. Request data: {request.POST}.")
        return redirect("hradmin:dashboard")

    messages.success(request, "Discord settings updated successfully.")

    return redirect("hradmin:dashboard")

@permissions_required(("hrapps.manage_hrapps"))
def update_discord_app_notification_settings(request):
    data = request.POST
    app_noti_enabled = data.get("enabled")
    app_noti_channel = data.get("channel")

    if app_noti_channel == "":
        app_noti_channel = None

    if app_noti_enabled == "on":
        app_noti_enabled = True
    else:
        app_noti_enabled = False

    try:
        discord_settings = HRAppDiscordSettings.get_solo()
        discord_settings.enable_application_notifications = app_noti_enabled
        discord_settings.application_notification_channel = app_noti_channel
        discord_settings.save()
    except Exception as e:
        logger.error(f"Failed to update discord notification settings: {e}")
        logger.exception(e)
        return False

    return True

@permissions_required(("hrapps.manage_hrapps",))
def update_discord_welcome_settings(request):
    data = request.POST
    welcomeEnabled = data.get("enabled")
    welcomeChannel = data.get("channel")
    welcomeMessage = data.get("message")
    welcomeIgnoredStates = [int(x) for x in data.getlist("ignored_states")]

    if welcomeChannel == "":
        welcomeChannel = None

    if welcomeEnabled == "on":
        welcomeEnabled = True
    else:
        welcomeEnabled = False

    try:
        discord_settings = HRAppDiscordSettings.get_solo()
        discord_settings.enable_welcome_messages = welcomeEnabled
        discord_settings.welcome_channel = welcomeChannel
        discord_settings.welcome_message = welcomeMessage
        discord_settings.ignored_states.set(welcomeIgnoredStates)
        discord_settings.save()
    except Exception as e:
        logger.error(f"Failed to update discord welcome settings: {e}")
        return False

    return True


@permissions_required(("hrapps.manage_hrapps",))
def update_discord_recruitment_settings(request):
    data = request.POST
    recruitmentEnabled = data.get("enabled")
    recruitmentChannel = data.get("channel")
    recruiterRole = data.get("role")
    recruitRole = data.get("rrole")

    if recruitmentChannel == "":
        recruitmentChannel = None

    if recruiterRole == "":
        recruiterRole = None

    if recruitRole == "":
        recruitRole = None

    if recruitmentEnabled == "on":
        recruitmentEnabled = True
    else:
        recruitmentEnabled = False

    try:
        discord_settings = HRAppDiscordSettings.get_solo()
        discord_settings.use_recruitment_threads = recruitmentEnabled
        discord_settings.recruitment_thread_channel = recruitmentChannel
        discord_settings.recruiter_role = recruiterRole
        discord_settings.recruit_role = recruitRole
        discord_settings.save()
    except Exception as e:
        logger.error(f"Failed to update discord recruitment settings: {e}")
        return False

    return True
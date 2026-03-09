import json

from allianceauth.eveonline.models import EveCharacter
from allianceauth.services.hooks import get_extension_logger
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.conf import settings

from . import Field, ResponseItem
from hrapps.models import FormResponse, Form, ResponseComment

logger = get_extension_logger(__name__)


def dashboard(request):
    user = request.user
    applications = FormResponse.objects.filter(user=user)

    recruiting_corps = Form.objects.filter(active=True).exclude(
        corporation__in=applications
        .filter(status__in=("pending", "under_review"))
        .values_list("form__corporation", flat=True)
    )

    ctx = {
        "applications": applications,
        "corp_forms": recruiting_corps
    }
    return render(request, "hrapps/main/dashboard.html", ctx)


def user_has_active_application(user, form):
    return (FormResponse.objects.filter(user=user, form=form).exists()
                or FormResponse.objects.filter(user=user, form__corporation=form.corporation).exists())


def apply(request, form_id):
    form = Form.objects.get(pk=form_id)
    if user_has_active_application(request.user, form):
        messages.error(request, "You already applied for this form.")
        return redirect("hrapps:dashboard")

    if request.method == "POST":
        body = request.body.decode("utf-8")
        logger.debug(body)
        body_json = json.loads(body)

        # Check if the user already has an application for this form or corp
        if user_has_active_application(request.user, form):
            messages.error(request, "You already applied for this form.")
            return HttpResponse(status=403)

        try:
            FormResponse.objects.create(form=form, user=request.user, response=body_json)
            return HttpResponse(status=201)
        except Exception as e:
            logger.error(e)
            return HttpResponse(status=500)

    fields = []
    for field in form.fields:
        fields.append(Field(**field))

    return render(request,
                  "hrapps/main/apply.html",
                  {"form": form, "fields": fields, "fields_json": json.dumps(fields, default=lambda o: o.__dict__())})


def get_corptools_chars(characters):
    if "corptools" in settings.INSTALLED_APPS:
        from corptools.models.audits import CharacterAudit

        char_audits = CharacterAudit.objects\
            .filter(character__in=characters)\
            .values_list("character__character_name", flat=True)
        return char_audits

    return None


def get_memberaudit_chars(characters):
    if "memberaudit" in settings.INSTALLED_APPS:
        from memberaudit.models.characters import Character

        char_audits = Character.objects\
            .filter(eve_character__in=characters)\
            .values_list("eve_character__character_name", flat=True)

        return char_audits

    return None


def view_application(request, application_id):
    application = FormResponse.objects.get(pk=application_id)
    app_comments = ResponseComment.objects.filter(response=application)
    characters = EveCharacter.objects\
        .filter(character_ownership__user=application.user)\
        .select_related()\
        .order_by('character_name')

    response_items = []
    for item in application.response["questions"]:
        response_items.append(ResponseItem(item["question"], item["answer"]))

    corptools = get_corptools_chars(characters) if "corptools" in settings.INSTALLED_APPS else None
    memberaudit = get_memberaudit_chars(characters) if "memberaudit" in settings.INSTALLED_APPS else None

    return render(request,
                  "hrapps/main/view.html",
                  {
                      "application": application,
                      "comments": app_comments,
                      "responses": response_items,
                      "characters": characters,
                      "corptools": corptools,
                      "memberaudit": memberaudit,
                  })
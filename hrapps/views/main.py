import json

from allianceauth.services.hooks import get_extension_logger
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages

from . import Field, get_application_context
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


def view_application(request, application_id):
    ctx = get_application_context(request, application_id)
    if ctx is None or request.user != ctx["application"].user:
        messages.error(request, "The requested application could not be found.")
        return redirect("hrapps:dashboard")

    return render(request, "hrapps/shared/view.html", ctx)
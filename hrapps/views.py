import json

from django.http import HttpResponse
from django.shortcuts import render
from allianceauth.services.hooks import get_extension_logger
from allianceauth.eveonline.models import EveCorporationInfo
from .models import Form

logger = get_extension_logger(__name__)


def get_or_create_corp(corporation_id):
    try:
        corp = EveCorporationInfo.objects.get(corporation_id=corporation_id)
    except EveCorporationInfo.DoesNotExist:
        EveCorporationInfo.objects.create_corporation(corporation_id)
        corp = EveCorporationInfo.objects.get(corporation_id=corporation_id)
    return corp


class Field:
    def __init__(self, type, question, options=None, required=False):
        self.type = type
        self.question = question
        self.required = required
        if options is not None:
            self.options = tuple(options)
        else:
            self.options = None


# Create your views here.
def dashboard(request):
    return render(request, "hrapps/dashboard.html")


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

    return render(request, "hrapps/builder.html", {"action": "Create"})


def edit_form(request, form_id):
    form = Form.objects.get(id=form_id)
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

    fields = tuple(fields)
    return render(request, "hrapps/builder.html", {"action": "Edit", "form": form, "fields": fields})


def forms_library(request):
    forms = Form.objects.all()
    ctx = {"forms": forms}
    return render(request, "hrapps/form_library.html", ctx)
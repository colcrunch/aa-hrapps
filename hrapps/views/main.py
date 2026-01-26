from django.shortcuts import render

from . import Field
from hrapps.models import FormResponse, Form


def dashboard(request):
    user = request.user
    applications = FormResponse.objects.filter(user=user)

    recruiting_corps = Form.objects.filter(active=True)

    ctx = {
        "applications": applications,
        "corp_forms": recruiting_corps
    }
    return render(request, "hrapps/main/dashboard.html", ctx)


def apply(request, form_id):
    form = Form.objects.get(pk=form_id)

    fields = []
    for field in form.fields:
        fields.append(Field(**field))

    return render(request, "hrapps/main/apply.html", {"form": form, "fields": fields})
import json

from allianceauth.authentication.decorators import permissions_required
from allianceauth.services.hooks import get_extension_logger
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages

from . import Field, get_application_context, add_comment, add_reply
from hrapps.models import FormResponse, Form, Attachment

logger = get_extension_logger(__name__)


def dashboard(request):
    user = request.user
    applications = FormResponse.objects.filter(user=user)

    recruiting_corps = Form.objects.filter(active=True).exclude(
        corporation__in=applications
        .filter(status__in=("pending", "under_review"))
        .values_list("form__corporation", flat=True)
    ).exclude(corporation__corporation_id=user.profile.main_character.corporation_id)

    ctx = {
        "applications": applications,
        "corp_forms": recruiting_corps
    }
    return render(request, "hrapps/main/dashboard.html", ctx)


def user_has_active_application(user, form):
    active_status = ("under_review", "accepted", "pending")
    return (FormResponse.objects.filter(user=user, form=form, status__in=active_status).exists()
                or FormResponse.objects\
                .filter(user=user, form__corporation=form.corporation, status__in=active_status).exists())


def apply(request, form_id):
    form = Form.objects.get(pk=form_id)

    fields = []
    for field in form.fields:
        fields.append(Field(**field))

    if request.method == "POST":
        logger.debug(request.FILES)
        body = request.POST.get("application")
        body_json = json.loads(body)
        logger.debug(body)

        has_files = bool(request.FILES)

        # Check if the user already has an application for this form or corp
        if user_has_active_application(request.user, form):
            messages.error(request, "You already applied for this form.")
            return HttpResponse(status=403)

        if has_files:
            logger.debug(request.FILES)
            file_fields = {field_id: field for field_id, field in enumerate(fields) if field.type == "image"}
            questions = body_json.get("questions")
            for file_field in request.FILES.keys():
                files = request.FILES.getlist(file_field)
                field_id = int(file_field.split("_")[1]) - 1

                if file_fields[field_id].attachmentLimit:
                    if len(files) > file_fields[field_id].attachmentLimit:
                        return HttpResponse(
                            status=400,
                            content=f"You cannot upload more than {file_fields[field_id].attachmentLimit} "
                                    f"files for the {file_fields[field_id].question} field"
                        )
                questions[field_id]["attachmentLimit"] = file_fields[field_id].attachmentLimit
                questions[field_id]["allowMultiple"] = file_fields[field_id].allowMultiple
                questions[field_id]["allowUpdates"] = file_fields[field_id].allowUpdates

        try:
            resp = FormResponse.objects.create(form=form, user=request.user, response=body_json)
            if not has_files:
                return HttpResponse(status=201)
        except Exception as e:
            logger.error(e)
            logger.exception(e)
            return HttpResponse(status=500)

        if has_files:
            for file_field in request.FILES.keys():
                files = request.FILES.getlist(file_field)
                field_id = int(file_field.split("_")[1])

                for file in files:
                    try:
                        Attachment.objects.create(response=resp, file=file, question_id=field_id)
                    except Exception as e:
                        resp.delete()
                        logger.error(e)
                        return HttpResponse(status=500)

        return HttpResponse(status=201)

    if user_has_active_application(request.user, form):
        messages.error(request, "You already applied for this form.")
        return redirect("hrapps:dashboard")

    return render(request,
                  "hrapps/main/apply.html",
                  {"form": form, "fields": fields, "fields_json": json.dumps(fields, default=lambda o: o.__dict__())})


def view_application(request, application_id):
    ctx = get_application_context(request, application_id)
    if ctx is None or request.user != ctx["application"].user:
        messages.error(request, "The requested application could not be found.")
        return redirect("hrapps:dashboard")

    if request.method == "POST":
        question = request.POST.get("question_id")
        app_id = ctx["application"].id

        files = request.FILES.getlist("file")
        if len(files) == 0:
            messages.error(request, "No files were uploaded.")
            return render(request, "hrapps/shared/view.html", ctx)

        limit = ctx["responses"][int(question) - 1].attachmentLimit
        attachments = Attachment.objects.filter(response_id=app_id, question_id=question).count()
        if len(files) > limit or attachments + len(files) > limit:
            messages.error(request, f"The total number of attachments for this question cannot exceed {limit}.")
            return render(request, "hrapps/shared/view.html", ctx)

        for file in files:
            try:
                Attachment.objects.create(response_id=app_id, file=file, question_id=question)
            except Exception as e:
                logger.error(e)
                return HttpResponse(status=500)

        new_ctx = get_application_context(request, application_id)
        messages.success(request, "File(s) uploaded successfully.")
        return render(request, "hrapps/shared/view.html", new_ctx)

    return render(request, "hrapps/shared/view.html", ctx)


def withdraw_application(request, application_id):
    try:
        app = FormResponse.objects.get(pk=application_id)
    except FormResponse.DoesNotExist:
        messages.error(request, "The requested application could not be found.")
        return redirect("hrapps:dashboard")

    if request.user != app.user:
        messages.error(request, "The requested application could not be found.")
        return redirect("hrapps:dashboard")

    app.status = "withdrawn"
    try:
        app.save()
    except Exception as e:
        messages.error(request, "There was an error when attempting to withdraw your application.")
        logger.error(f"An error occurred while attempting to withdraw FormResponse {application_id}")
        logger.error(e)
        return redirect("hrapps:dashboard")

    messages.success(request, "Application successfully withdrawn.")
    return redirect("hrapps:dashboard")


@permissions_required(("hrapps.create_comment",))
def create_comment(request, application_id):
    success = add_comment(request, application_id)
    if success:
        messages.success(request, "Comment added.")
    else:
        messages.error(request, "Unable to add comment.")
    return redirect("hrapps:view", application_id)


@permissions_required(("hrapps.create_comment",))
def create_reply(request, application_id, comment_id):
    success = add_reply(request, application_id, comment_id)
    if success:
        messages.success(request, "Reply added.")
    else:
        messages.error(request, "Unable to add reply.")
    return redirect("hrapps:view", application_id)
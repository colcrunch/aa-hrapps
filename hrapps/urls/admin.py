from django.contrib.auth.decorators import permission_required
from django.urls import re_path

from hrapps.views import admin as views

app_name = 'hradmin'

urlpatterns = [
    re_path(r"^$", views.dashboard, name="dashboard"),
    re_path(r"^form/create/$", views.create_form, name="create_form"),
    re_path(r"^form/library/$", views.forms_library, name="forms_library"),
    re_path(r"^form/(?P<form_id>\d+)/edit/$", views.edit_form, name="edit_form"),
    re_path(r"^form/(?P<form_id>\d+)/copy/$", views.copy_form, name="copy_form"),
    re_path(r"^form/(?P<form_id>\d+)/delete/$", views.delete_form, name="delete_form"),
    re_path(r"^form/(?P<form_id>\d+)/$", views.view_form, name="view_form"),
    re_path(r"^resp/(?P<response_id>\d+)/$", views.view_response, name="view_response"),
    re_path(r"^resp/(?P<response_id>\d+)/comment/$", views.create_comment, name="create_comment"),
    re_path(r"^resp/(?P<response_id>\d+)/approve/$", views.approve_response, name="approve_response"),
    re_path(r"^resp/(?P<response_id>\d+)/reject/$", views.reject_response, name="reject_response"),
    re_path(r"^resp/(?P<response_id>\d+)/pend/$", views.pend_response, name="pend_response"),
    re_path(r"^resp/(?P<response_id>\d+)/review/$", views.review_status_response, name="review_status_response"),
    re_path(r"^resp/(?P<response_id>\d+)/claim/recruiter/$", views.claim_recruiter, name="claim_recruiter"),
    re_path(r"^resp/(?P<response_id>\d+)/claim/reviewer/$", views.claim_reviewer, name="claim_reviewer"),
]

for url in urlpatterns:
    url.callback = permission_required("hrapps.access_hradmin")(url.callback)
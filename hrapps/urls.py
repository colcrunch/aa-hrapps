from django.urls import re_path

from . import views

app_name = 'hrapps'

urlpatterns = [
    re_path(r"^$", views.dashboard, name="dashboard"),
    re_path(r"^form/create/$", views.create_form, name="create_form"),
    re_path(r"^form/library/$", views.forms_library, name="forms_library"),
    re_path(r"^form/(?P<form_id>\d+)/edit/$", views.edit_form, name="edit_form"),
]
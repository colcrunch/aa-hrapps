from django.urls import re_path

from . import views

app_name = 'hrapps'

urlpatterns = [
    re_path(r"^$", views.dashboard, name="dashboard"),
    re_path(r"^form/create/$", views.create_form, name="create_form"),
]
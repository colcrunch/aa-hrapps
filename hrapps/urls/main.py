from django.urls import re_path

from hrapps.views import main as views

app_name = 'hrapps'

urlpatterns = [
    re_path(r"^$", views.dashboard, name="dashboard"),
    re_path(r"^apply/(?P<form_id>\d+)/$", views.apply, name="apply"),
    re_path(r"^view/(?P<application_id>\d+)/$", views.view_application, name="view"),
]
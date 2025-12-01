from django.urls import re_path

from . import views

app_name = 'hrapps'

urlpatterns = [
    re_path(r"^$", views.dashboard, name="dashboard"),
]
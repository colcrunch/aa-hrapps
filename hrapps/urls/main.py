from django.urls import re_path

from hrapps.views import main as views

app_name = 'hrapps'

urlpatterns = [
    re_path(r"^$", views.dashboard, name="dashboard"),
]
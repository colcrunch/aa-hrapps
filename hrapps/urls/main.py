from django.contrib.auth.decorators import permission_required
from django.urls import re_path

from hrapps.views import main as views

app_name = 'hrapps'

urlpatterns = [
    re_path(r"^$", views.dashboard, name="dashboard"),
    re_path(r"^apply/(?P<form_id>\d+)/$", views.apply, name="apply"),
    re_path(r"^view/(?P<application_id>\d+)/$", views.view_application, name="view"),
    re_path(r"^withdraw/(?P<application_id>\d+)/$", views.withdraw_application, name="withdraw"),
    re_path(r"^comment/(?P<application_id>\d+)/$", views.create_comment, name="create_comment"),
    re_path(r"^comment/(?P<application_id>\d+)/reply/(?P<comment_id>\d+)/$", views.create_reply, name="create_reply"),
]

for url in urlpatterns:
    url.callback = permission_required("hrapps.access_hrapps")(url.callback)
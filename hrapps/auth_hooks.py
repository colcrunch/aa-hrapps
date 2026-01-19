from django.utils.translation import gettext_lazy as _

from allianceauth import hooks
from allianceauth.menu.hooks import MenuItemHook
from allianceauth.services.hooks import UrlHook

from .urls import admin, main

class HRAdminMenuItemHook(MenuItemHook):
    def __init__(self):
        MenuItemHook.__init__(
            self,
            _("HR Apps Admin"),
            "fa-solid fa-id-card-clip",
            "hradmin:dashboard",
            navactive=["hradmin:"]
        )

        self.admin_perms = (
            "hrappperms.manage_hrapps",
            "formresponse.view_all_responses",
            "formresponse.view_corp_responses",
            "form.manage_all_forms",
            "form.manage_corp_forms",
        )

    def render(self, request):
        if any(request.user.has_perm(perm) for perm in self.admin_perms):
            return MenuItemHook.render(self, request)
        return ''


class HRMainMenuItemHook(MenuItemHook):
    def __init__(self):
        MenuItemHook.__init__(
            self,
            _("HR Applications"),
            "fa-solid fa-id-card-clip",
            "hrapps:dashboard",
            navactive=["hrapps:"]
        )

    def render(self, request):
        if request.user.has_perm("hrappperms.access_hrapps"):
            return MenuItemHook.render(self, request)
        return ''

@hooks.register("menu_item_hook")
def register_admin_menu():
    return  HRAdminMenuItemHook()

@hooks.register("url_hook")
def register_admin_urls():
    return UrlHook(admin, "hradmin", "^hradmin/")

@hooks.register("menu_item_hook")
def register_user_menu():
    return  HRMainMenuItemHook()

@hooks.register("url_hook")
def register_user_urls():
    return UrlHook(main, "hrapps", "^hrapps/")
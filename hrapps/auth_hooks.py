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

    def render(self, request):
        if request.user.has_perm("hrapps.access_hradmin"):
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
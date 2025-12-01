from django.utils.translation import gettext_lazy as _

from allianceauth import hooks
from allianceauth.menu.hooks import MenuItemHook
from allianceauth.services.hooks import UrlHook

from . import urls

class HRMenuItemHook(MenuItemHook):
    def __init__(self):
        MenuItemHook.__init__(
            self,
            _("HR Apps"),
            "fa-solid fa-id-card-clip",
            "hrapps:dashboard",
            navactive=["hrapps:"]
        )

    def render(self, request):
        if request.user.has_perm("hrappperms.access_hrapps") or request.user.has_perm("hrappperms.manage_hrapps"):
            return MenuItemHook.render(self, request)
        return ''

@hooks.register("menu_item_hook")
def register_menu():
    return  HRMenuItemHook()

@hooks.register("url_hook")
def register_urls():
    return UrlHook(urls, "hrapps", "^hrapps/")
from allianceauth.services.hooks import get_extension_logger
from discord import SlashCommandGroup

from discord.ext import commands

from aadiscordbot.cogs.utils.decorators import sender_has_perm
from aadiscordbot.app_settings import get_all_servers, get_site_url

from hrapps.models import HRAppDiscordSettings

logger = get_extension_logger(__name__)

class HRApps(commands.Cog):
    """
    A cog to integrate with the HRApps app.
    """

    def __init__(self, bot):
        self.settings = HRAppDiscordSettings.get_solo()
        self.bot = bot

    hrapps_commands = SlashCommandGroup(
        "hrapps",
        "HRApps",
        guild_ids=get_all_servers()
    )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        logger.info(f"Member joined the server.")
        print("XX")
        pass


def setup(bot):
    bot.add_cog(HRApps(bot))
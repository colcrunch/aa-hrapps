from collections import defaultdict

import discord.ui
from aadiscordbot.utils.auth import get_auth_user
from allianceauth.services.hooks import get_extension_logger
from aadiscordbot.app_settings import get_all_servers, get_site_url
from aadiscordbot.cogs.utils.exceptions import NotAuthenticated
from discord import SlashCommandGroup
from discord.ext import commands
from hrapps.models import HRAppDiscordSettings

logger = get_extension_logger(__name__)


async def add_recruit_role(member, guild, role_id):
    role = guild.get_role(role_id)
    await member.add_roles(role)


async def create_recruitment_thread(member, guild, channel_id, recruiter_role_id):
    logger.debug(f"Creating recruitment thread for {member.name}")
    channel = guild.get_channel(channel_id)
    recruiter_role = guild.get_role(recruiter_role_id)
    thread = await channel.create_thread(
        name=f"Recruitment: {member.name}",
        type=discord.ChannelType.public_thread
    )
    logger.debug(f"Sending recruiter notification message in thread for {member.name}")
    await thread.send(f"ATTN: {recruiter_role.mention}\n{member.mention} has indicated they are interested in joining.")


class RecruitButtonView(discord.ui.View):
    def __init__(self, member=None):
        super().__init__(timeout=None)
        self.member = member
        self.settings = HRAppDiscordSettings.get_solo()

    @discord.ui.button(label="Recruit Me", style=discord.ButtonStyle.green)
    async def recruit_button(self, button, interaction):
        if interaction.user != self.member:
            await interaction.response.send_message("You can not make this decision for others.", ephemeral=True)
            return

        logger.debug(f"Adding recruit role to {self.member.name}")
        await add_recruit_role(self.member, interaction.guild, self.settings.recruit_role)
        await create_recruitment_thread(
            self.member,
            interaction.guild,
            self.settings.recruitment_thread_channel,
            self.settings.recruiter_role
        )

        await interaction.response.edit_message(view=None)


    @discord.ui.button(label="No Thanks")
    async def cancel_button(self, button, interaction):
        if interaction.user != self.member:
            await interaction.response.send_message("You can not make this decision for others.", ephemeral=True)
            return
        await interaction.response.edit_message(view=None)
        await interaction.followup.send(
            "If you change your mind later, simply run the /recruit_me command.",
            ephemeral=True
        )


class HRApps(commands.Cog):
    """
    A cog to integrate with the HRApps app.
    """

    def __init__(self, bot):
        self.settings = HRAppDiscordSettings.get_solo()
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        logger.debug(f"Member joined the server.")
        # Check if the user is part of an ignored state, if so we can return, no need to welcome.
        try:
            user = get_auth_user(member._user, member.guild)
            if user.profile.state in self.settings.ignored_states.all():
                logger.debug(f"User is in ignored state, no need to welcome.")
                return
        except NotAuthenticated:
            # User is not found, continue
            logger.debug(f"User not found, continuing.")
            pass
        except Exception as e:
            logger.error(f"Error checking if user is in ignored state: {e}")
            return

        # Welcome the user
        logger.debug(f"Welcoming user {member.name}")
        logger.debug(f"Use Recruitment Threads on? {self.settings.use_recruitment_threads}")
        welcome_channel = self.bot.get_channel(self.settings.welcome_channel)
        recruit_view = RecruitButtonView(member) if self.settings.use_recruitment_threads else None
        await welcome_channel.send(
            self.settings.welcome_message.format_map(
                defaultdict(
                    lambda:"",
                    user_mention=member.mention,
                    auth_url=get_site_url()
                )
            ),
            view=recruit_view
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not self.settings.use_recruitment_threads:
            return

        logger.debug(f"Message type: {message.type}")
        if message.channel == message.guild.get_channel(self.settings.recruitment_thread_channel) and message.type == discord.MessageType.thread_created:
            logger.debug(f"Found recruitment thread, deleting creation message for privacy. {message.id}")
            await message.delete()
            return

    @commands.slash_command(name="recruit_me", description="Begin the recruitment process.", guild_ids=get_all_servers())
    async def recruit_me(self, ctx):
        await add_recruit_role(ctx.author, ctx.guild, self.settings.recruit_role)
        await create_recruitment_thread(
            ctx.author,
            ctx.guild,
            self.settings.recruitment_thread_channel,
            self.settings.recruiter_role
        )
        await ctx.respond("Your recruitment thread has been created.", ephemeral=True)



def setup(bot):
    bot.add_cog(HRApps(bot))
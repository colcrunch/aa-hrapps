import asyncio
import json
from collections import defaultdict

import discord.ui
import redis.asyncio as aioredis
from django.conf import settings
from allianceauth.utils.cache import get_redis_client
from aadiscordbot.utils.auth import get_auth_user
from allianceauth.services.hooks import get_extension_logger
from aadiscordbot.app_settings import get_all_servers, get_site_url
from aadiscordbot.cogs.utils.exceptions import NotAuthenticated
from discord.ext import commands
from hrapps.models import HRAppDiscordSettings, FormResponse, ResponseComment
from allianceauth.eveonline.evelinks import eveimageserver

logger = get_extension_logger(__name__)


async def add_recruit_role(member, guild, role_id):
    logger.debug(f"Adding recruit role to {member.name}")
    role = guild.get_role(role_id)
    await member.add_roles(role)


async def check_active_threads(member, guild, channel_id):
    logger.debug(f"Checking active threads for {member.name}")
    channel = guild.get_channel(channel_id)
    thread = discord.utils.find(lambda t: member.name in t.name, channel.threads)
    if thread:
        return thread.id
    return None


async def create_recruitment_thread(member, guild, channel_id, recruiter_role_id):
    logger.debug(f"Creating recruitment thread for {member.name}")
    channel = guild.get_channel(channel_id)
    recruiter_role = guild.get_role(recruiter_role_id)
    thread = await channel.create_thread(
        name=f"Recruitment: {member.name}",
        type=discord.ChannelType.public_thread
    )
    logger.debug(f"Sending recruiter notification message in thread for {member.name}")
    await thread.send(f"*ATTN: {recruiter_role.mention}*\n\n{member.mention} has indicated they are interested in joining.")


class RecruitButtonView(discord.ui.View):
    def __init__(self, bot, member=None):
        super().__init__(timeout=None)
        self.bot = bot
        self.member = member

    @discord.ui.button(label="Recruit Me", style=discord.ButtonStyle.green, custom_id="hrapps_recruit_button")
    async def recruit_button(self, button, interaction):
        if self.member is None:
            # If the bot is restarted then existing views will lose the member attribute. In this case we don't have a
            # reliable way to know who the user is that the welcome message was targeting as the user mention may not
            # be the first one.
            command = self.bot.get_application_command("recruit_me")
            await interaction.response.edit_message(view=None)
            await interaction.followup.send(
                f"Something went wrong processing your request. "
                f"Please use the </recruit_me:{command.id}> command instead.",
                ephemeral=True
            )
            return
        if interaction.user != self.member:
            await interaction.response.send_message("You can not make this decision for others.", ephemeral=True)
            return
        settings = HRAppDiscordSettings.get_solo()

        await add_recruit_role(self.member, interaction.guild, settings.recruit_role)
        existing_thread = await check_active_threads(self.member, interaction.guild, settings.recruitment_thread_channel)
        if existing_thread:
            channel = interaction.guild.get_channel(existing_thread)
            await channel.send(f"{self.member.mention} here is your existing recruitment thread!")
        else:
            await create_recruitment_thread(
                self.member,
                interaction.guild,
                settings.recruitment_thread_channel,
                settings.recruiter_role
            )

        await interaction.response.edit_message(view=None)


    @discord.ui.button(label="No Thanks", custom_id="hrapps_cancel_button")
    async def cancel_button(self, button, interaction):
        if interaction.user != self.member:
            await interaction.response.send_message("You can not make this decision for others.", ephemeral=True)
            return
        command = self.bot.get_application_command("recruit_me")
        await interaction.response.edit_message(view=None)
        await interaction.followup.send(
            f"If you change your mind later, simply run the </recruit_me:{command.id}> command.",
            ephemeral=True
        )


class HRApps(commands.Cog):
    """
    A cog to integrate with the HRApps app.
    """

    def __init__(self, bot):
        self.settings = HRAppDiscordSettings.get_solo()
        self.bot = bot

        redis_client = get_redis_client()
        rkwargs = redis_client.connection_pool.connection_kwargs
        rkwargs["decode_responses"] = True
        rkwargs.pop("parser_class", None)
        rkwargs.pop("password", None)

        self.redis_client = aioredis.Redis(**rkwargs)
        self.pubsub = self.redis_client.pubsub()
        self.listener_task = self.bot.loop.create_task(self.listen_to_mq())
        logger.debug("Initialized HRApp cog.")

    async def listen_to_mq(self):
        await self.pubsub.subscribe("hrapp_discord_settings")
        if self.settings.enable_application_notifications:
            await self.pubsub.subscribe("hrapp_application_notifications")
            await self.pubsub.subscribe("hrapp_comment_notifications")
        logger.debug("Listening for HRApp settings updates.")

        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    logger.debug("Received redis message")
                    data = json.loads(message["data"])
                    action = data.get("action")

                    if action == "settings_updated":
                        logger.debug("HRApp settings updated, updating local settings.")
                        await self.update_settings()
                    if action == "new application":
                        logger.debug("New HRApp application detected, sending notification.")
                        await self.send_new_app_notification(data.get("app_pk"))
                    if action == "new comment":
                        logger.debug("New HRApp comment detected, sending notification.")
                        await self.send_new_comment_notification(data.get("comment_pk"))
        except asyncio.CancelledError:
            logger.debug("Cancelled listening for HRApp settings updates.")
        except Exception as e:
            logger.error(f"Error listening for HRApp settings updates: {e}")
            logger.exception(e)

    async def send_new_app_notification(self, app_pk):
        channel = self.bot.get_channel(self.settings.application_notification_channel)
        application = FormResponse.objects.get(pk=app_pk)
        embed = discord.Embed(
            title="New Application Submitted",
            description=f"{application.user.profile.main_character.character_name} "
                        f"has applied to join {application.form.corporation.corporation_name}",
            colour=discord.Colour.green()
        )
        embed.set_author(name=application.user.profile.main_character.character_name,
                         icon_url=eveimageserver.character_portrait_url(application.user.profile.main_character.character_id))
        embed.set_thumbnail(url=eveimageserver.corporation_logo_url(application.form.corporation.corporation_id, 128))
        embed.set_footer(text=f"{self.bot.user.name} via AllianceAuth HRApps", icon_url=self.bot.user.display_avatar.url)
        embed.add_field(name=" ", value="⠀")
        embed.add_field(name="App Link", value=f"[Click Here]({settings.SITE_URL}/hradmin/resp/{app_pk})", inline=False)

        await channel.send(embed=embed)

    async def send_new_comment_notification(self, comment_pk):
        channel = self.bot.get_channel(self.settings.application_notification_channel)
        comment = ResponseComment.objects.get(pk=comment_pk)
        application = comment.response
        embed = discord.Embed(
            title=f"New Comment",
            description=f"{comment.user.profile.main_character.character_name} commented on "
                        f"{application.user.profile.main_character.character_name}'s application.",
            colour=discord.Colour.blurple()
        )
        embed.set_author(name=comment.user.profile.main_character.character_name,
                         icon_url=eveimageserver.character_portrait_url(comment.user.profile.main_character.character_id))
        embed.set_footer(text=f"{self.bot.user.name} via AllianceAuth HRApps", icon_url=self.bot.user.display_avatar.url)
        embed.add_field(name="Private Comment?", value=f"{comment.private}", inline=False)
        embed.add_field(name="Comment", value=f"{comment.content}", inline=False)
        embed.add_field(name=" ", value=" ", inline=False)

        await channel.send(embed=embed)

    async def update_settings(self):
        self.settings = HRAppDiscordSettings.get_solo()

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
        recruit_view = RecruitButtonView(self.bot, member) if self.settings.use_recruitment_threads else None
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
        if message.type == discord.MessageType.thread_created and message.channel == message.guild.get_channel(self.settings.recruitment_thread_channel):
            logger.debug(f"Found recruitment thread, deleting creation message for privacy. {message.id}")
            await message.delete()
            return

    @commands.Cog.listener()
    async def on_ready(self):
        logger.debug("HRApp cog is ready.")
        self.bot.add_view(RecruitButtonView(self.bot))

    @commands.slash_command(name="recruit_me", description="Begin the recruitment process.", guild_ids=get_all_servers())
    async def recruit_me(self, ctx):
        try:
            user = get_auth_user(ctx.author, ctx.guild)
            if user.profile.state in self.settings.ignored_states.all():
                return await ctx.respond("You are not eligible for recruitment.", ephemeral=True)
        except NotAuthenticated:
            pass

        await add_recruit_role(ctx.author, ctx.guild, self.settings.recruit_role)
        existing_thread = await check_active_threads(ctx.author, ctx.guild, self.settings.recruitment_thread_channel)
        if existing_thread:
            print(existing_thread)
            channel = await self.bot.fetch_channel(existing_thread)
            print(channel)
            await channel.send(f"{ctx.author.mention} here is your existing recruitment thread!")
            return await ctx.respond("You have already started the recruitment process.\n"
                                     "Please check for your recruitment thread.", ephemeral=True)
        await create_recruitment_thread(
            ctx.author,
            ctx.guild,
            self.settings.recruitment_thread_channel,
            self.settings.recruiter_role
        )
        return await ctx.respond("Your recruitment thread has been created.", ephemeral=True)


def setup(bot):
    bot.add_cog(HRApps(bot))
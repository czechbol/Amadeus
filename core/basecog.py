import traceback
from datetime import datetime
from datetime import timezone

import discord
from discord.ext import commands

from core.config import config
from core.text import text


class Basecog(commands.Cog):
    """Main cog class"""

    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.slave = None
        self.guild = None
        self.role_mod = None
        self.role_verify = None
        self.roles_elevated = None

    # OBJECT GETTERS
    def getGuild(self):
        if self.guild is None:
            self.guild = self.bot.get_guild(config.guild_id)
        return self.guild

    def getSlave(self):
        if self.slave is None:
            self.slave = self.bot.get_guild(config.slave_id)
        return self.slave

    def getModRole(self):
        if self.role_mod is None:
            self.role_mod = self.getGuild().get_role(config.role_mod)
        return self.role_mod

    def getVerifyRole(self):
        if self.role_verify is None:
            self.role_verify = self.getGuild().get_role(config.role_verify)
        return self.role_verify

    def getElevatedRoles(self):
        if self.roles_elevated is None:
            self.roles_elevated = [self.getGuild().get_role(x) for x in config.roles_elevated]
        return self.roles_elevated

    # Helper functions
    def create_embed(self, ctx, error=False, **kwargs):
        if "color" not in kwargs:
            kwargs["color"] = config.color
        if "timestamp" not in kwargs:
            kwargs["timestamp"] = datetime.now(tz=timezone.utc)

        author_name = f"{ctx.message.author.name}#{ctx.message.author.discriminator}"

        embed = discord.Embed(**kwargs)
        if not error:
            embed.set_footer(
                text=text.fill("basecog", "embed footer", user=author_name),
                icon_url=ctx.message.author.avatar_url,
            )
        else:
            embed.set_footer(
                text=text.fill("basecog", "error footer", user=author_name),
                icon_url=ctx.message.author.avatar_url,
            )
        return embed

    # Utils
    async def guildlog(self, ctx, action: str, quote: bool = True, msg=None):
        """Log event"""
        channel = self.getGuild().get_channel(config.channel_guildlog)
        author = self.getGuild().get_member(ctx.author.id)
        if author.top_role.id in config.roles_elevated:
            user = "{r} **{u}**".format(u=author.name, r=author.top_role.name.lower())
        else:
            user = ctx.author.mention
        if isinstance(ctx.channel, discord.DMChannel):
            message = "**{}** by {} in DM".format(action, user)
        else:
            message = "**{}** by {} in {}".format(action, user, ctx.channel.mention)

        if ctx.guild and ctx.guild.id != config.guild_id:
            message += " (**{}**/{})".format(ctx.guild.name, ctx.guild.id)

        if msg is not None or quote is not None:
            message += ": "
        if msg is not None:
            if type(msg).__name__ == "str":
                message += msg
            else:
                message += type(msg).__name__
        if quote:
            message += "\n> _{}_".format(ctx.message.content)
        await channel.send(message)
        # TODO Save to log

    async def roomCheck(self, ctx: commands.Context):
        """Send a message to prevent bot spamming"""
        if isinstance(ctx.channel, discord.DMChannel):
            return
        botspam = self.getGuild().get_channel(config.channel_botspam)
        if ctx.channel.id not in config.bot_allowed:
            await ctx.send(text.fill("basecog", "botroom redirect", user=ctx.author, channel=botspam))

    async def deleteCommand(self, message, now: bool = True):
        """Try to delete the context message.

        now: Do not wait for message delay
        """
        delay = 0.0 if now else config.delay_embed
        try:
            if not isinstance(message, discord.Message):
                message = message.message
            await message.delete(delay=delay)
        except discord.HTTPException as err:
            self.logException(message, err)

    # Embeds
    async def throwError(self, ctx: commands.Context, err):
        """Show an embed and log the error"""
        # Get error information

        err = getattr(err, "original", err)
        err_type = type(err).__name__
        err_trace = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        err_title = "{}: {}".format(ctx.author, ctx.message.content)

        # Do the debug
        if config.debug >= 1:
            print("ERROR OCCURED: " + err_title)
            print("ERROR TRACE: " + err_trace)
        if config.debug >= 2:
            await self.sendLong(ctx, "[debug=2] Error: " + err_title + "\n" + err_trace, code=True)
        # Clean the input
        content = ctx.message.content
        content = content if len(content) < 600 else content[:600]

        if len(err_trace) > 600:
            err_trace = err_trace[-600:]

        # Construct the error embed
        embed = self.create_embed(ctx, error=True, title=err_type, color=config.color_error)
        embed.add_field(name="Command", value=content, inline=True)
        embed.add_field(name="Error trace", value=f"```{err_trace}```", inline=False)

        await ctx.send(embed=embed)
        await self.deleteCommand(ctx, now=True)

    async def throwNotification(self, ctx: commands.Context, msg: str, pin: bool = False):
        """Show an embed with a message."""
        msg = str(msg)
        # Do the debug
        title = "{}: {}".format(ctx.author, ctx.message.content)
        if config.debug >= 1:
            print("NOTIFICATION: " + title)
            print("NOTIFY TRACE: " + msg)
        if config.debug >= 2:
            await self.sendLong(ctx, "[debug=2] Notification: " + title + "\n" + msg, code=True)

        # Clean the input
        content = ctx.message.content
        if len(str(content)) > 512:
            content = str(content)[:512]
        content = content if len(content) < 512 else content[:512]

        # Construct the notification embed
        embed = self.create_embed(ctx, color=config.color_notify)
        embed.add_field(name="Notification", value=msg, inline=False)
        embed.add_field(name="Command", value=content, inline=False)
        await ctx.send(embed=embed)
        await self.deleteCommand(ctx, now=True)
        # TODO Should we log this?

    # TODO Move helper functions here
    # HELPER FUNCTIONS
    async def sendLong(self, ctx: commands.Context, message: str, code: bool = False):
        """Send messages that may exceed the 2000-char limit

        message: The text to be sent
        code: Whether to format the output as a code
        """
        message = list(message[0 + i : 1960 + i] for i in range(0, len(message), 1960))
        for m in message:
            if code:
                await ctx.send("```\n{}```".format(m))
            else:
                await ctx.send(m)

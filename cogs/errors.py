import traceback

from discord.ext import commands

from core.config import config
from core import basecog
from core.text import text


class Errors(basecog.Basecog):
    def __init__(self, bot):
        super().__init__(bot)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        """Handle errors"""
        if hasattr(ctx.command, "on_error") or hasattr(ctx.command, "on_command_error"):
            return

        error = getattr(error, "original", error)

        printed = False
        if config.debug == 2:
            print("".join(traceback.format_exception(type(error), error, error.__traceback__)))
            printed = True

        # fmt: off
        if isinstance(error, commands.MissingPermissions):
            await self.throwNotification(ctx, text.get("error", "no user permission"))
            await self.guildlog(ctx, self._getCommandSignature(ctx), quote=True, msg=error)
            return

        elif isinstance(error, commands.BotMissingPermissions):
            await self.throwNotification(ctx, text.get("error", "no bot permission"))
            await self.guildlog(ctx, self._getCommandSignature(ctx), quote=True, msg=error)
            return

        elif isinstance(error, commands.CommandOnCooldown):
            await self.throwNotification(ctx, text.fill("error", "cooldown", time=int(error.retry_after)))
            return

        elif isinstance(error, commands.CheckFailure):
            # TODO Extract requirements and add them to the embed
            await self.throwNotification(ctx, text.get("error", "no requirements"))
            await self.guildlog(ctx, self._getCommandSignature(ctx), quote=True, msg=error)
            return

        elif isinstance(error, commands.BadArgument):
            await self.throwNotification(ctx, text.get("error", "argument"))
            return
        elif isinstance(error, commands.ExpectedClosingQuoteError):
            await self.throwNotification(ctx, text.get("error", "argument"))
            return

        elif isinstance(error, commands.CommandNotFound):
            if not ctx.message.content[0] in config.prefixes:
                await self.throwNotification(ctx, text.get("error", "no command"))
            return

        elif isinstance(error, commands.ExtensionError):
            await self.throwError(ctx, error)
            return

        elif isinstance(error, commands.MissingRequiredArgument):
            await self.throwNotification(ctx, error)
            await self.guildlog(ctx, "Missing argument", quote=True, msg=error)
            return
        # fmt: on
        if ctx.channel.id == config.channel_botdev:
            return
        # display error message
        await self.throwError(ctx, error)
        await self.guildlog(ctx, "on_command_error", quote=True, msg=error)

        output = "Ignoring exception in command {}: \n\n".format(ctx.command)
        output += "".join(traceback.format_exception(type(error), error, error.__traceback__))
        # print traceback to stdout
        if not printed:
            print(output)
        # send traceback to dedicated channel
        channel = self.bot.get_channel(config.channel_botdev)
        output = list(output[0 + i : 1960 + i] for i in range(0, len(output), 1960))
        if channel is not None:
            for message in output:
                await channel.send("```\n{}```".format(message))


def setup(bot):
    bot.add_cog(Errors(bot))

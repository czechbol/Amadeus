import traceback

import discord
from discord.ext import commands

from core.emote import emote
from core.config import config
from core import check, help, basecog

from features import presence
from repository.database import session
from repository.database import database
from repository.database.vote import Vote  # noqa F401
from repository.database.remind import Reminder  # noqa F401
from repository.database.user_channels import UserChannel  # noqa F401
from repository.database.unverify import Unverify  # noqa F401
from repository.database.tempverify import Tempverify  # noqa F401
from repository.database.emote import Emote  # noqa F401

intents = discord.Intents.default()
intents.members = True
intents.presences = True

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(*config.prefixes),
    help_command=help.Help(),
    allowed_mentions=discord.AllowedMentions(roles=False, everyone=False, users=True),
    intents=intents,
)

presence = presence.Presence(bot)
basecog = basecog.Basecog(bot)


@bot.event
async def on_ready():
    """If Amadeus is ready."""
    if config.debug < 1:
        login = "Logged in"
    else:
        login = "Logged with debug(" + str(config.debug) + ")"
    await basecog.log(level="info", message=login)
    await presence.set_presence()


@bot.event
async def on_error(event, *args, **kwargs):
    channel = bot.get_channel(config.channel_botdev)
    output = traceback.format_exc()
    print(output)
    output = list(output[0 + i : 1960 + i] for i in range(0, len(output), 1960))
    if channel is not None:
        for message in output:
            await channel.send("```\n{}```".format(message))


@commands.check(check.is_mod)
@bot.command()
async def load(ctx, extension):
    extension = extension.lower()
    try:
        bot.load_extension(f"cogs.{extension}")
        await ctx.send(f"Rozšíření **{extension}** načteno.")
        await basecog.log(level="info", message=f"Cog {extension} loaded")
    except Exception as e:
        await ctx.send(f"Načtení rozšíření **{extension}** se nezdařilo.")
        await basecog.log(level="error", message="Cog loading failed" + str(e))


@commands.check(check.is_mod)
@bot.command()
async def unload(ctx, extension):
    extension = extension.lower()
    try:
        bot.unload_extension(f"cogs.{extension}")
        await ctx.send(f"Rozšíření **{extension}** odebráno.")
        await basecog.log(level="info", message=f"Cog {extension} unloaded")
    except Exception as e:
        await ctx.send(f"Odebrání rozšíření **{extension}** se nezdařilo.")
        await basecog.log(level="error", message="Cog loading failed" + str(e))


@commands.check(check.is_mod)
@bot.command()
async def reload(ctx, extension):
    extension = extension.lower()
    try:
        bot.reload_extension(f"cogs.{extension}")
        await ctx.send(f"Rozšíření **{extension}** aktualizováno.")
        await basecog.log(level="info", message=f"Cog {extension} reloaded")
    except Exception as e:
        await ctx.send(f"Aktualizace rozšíření **{extension}** se nepovedla.")
        await basecog.log(level="error", message="Cog loading failed" + str(e))


@reload.error
@load.error
@unload.error
async def missing_arg_error(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send("Nesprávný počet argumentů" + emote.sad)


# database.base.metadata.drop_all(database.db)
database.base.metadata.create_all(database.db)
session.commit()  # Making sure

bot.load_extension("cogs.errors")
print("Meta ERRORS extension loaded.")
for extension in config.extensions:
    bot.load_extension(f"cogs.{extension}")
    print("{} extension loaded.".format(extension.upper()))

bot.run(config.key)

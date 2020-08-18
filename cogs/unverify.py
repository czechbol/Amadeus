import re
import asyncio
from datetime import datetime
from datetime import timedelta
from dateparser.search import search_dates

import discord
from discord.ext import tasks, commands

from core import basecog
from core.text import text
from core.config import config
from repository import unverify_repo


repository = unverify_repo.UnverifyRepository()


class Unverify(basecog.Basecog):
    """Voting based commands"""

    def __init__(self, bot):
        self.bot = bot
        self.unverify_loop.start()

    def cog_unload(self):
        self.unverify_loop.cancel()

    @tasks.loop(seconds=10.0)
    async def unverify_loop(self):
        repo = repository.get_waiting()
        if repo != []:
            for row in repo:
                duration = row.new_date - datetime.now()
                duration_in_s = duration.total_seconds()
                if row.new_date < datetime.now():
                    await self.reverify_user(row)
                elif duration_in_s < 10:
                    await self.reverify_user(row, time=duration_in_s)
        repo = repository.get_finished()
        if repo != []:
            for row in repo:
                if row.new_date < (datetime.now() - timedelta(days=7)):
                    await self.log(
                        level="debug",
                        message=f"Deleting unverify from db: ID: {row.idx}, time: {row.new_date}, status: {row.status}, \nmessage: {row.message}",
                    )
                    repository.delete(row.idx)

    @unverify_loop.before_loop
    async def before_unverify_loop(self):
        if not self.bot.is_ready():
            await self.log(level="info", message="Unverify loop - waiting until ready()")
            await self.bot.wait_until_ready()

    async def parse_datetime(self, arg):
        dates = search_dates(
            arg.replace(".", "-"),
            languages=["en"],
            settings={"PREFER_DATES_FROM": "future", "PREFER_DAY_OF_MONTH": "first", "DATE_ORDER": "DMY"},
        )
        if dates is None:
            return None, ""

        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

        for day in weekdays:
            if str("next " + day) in arg.lower() and day in dates[0][0].lower():
                date = dates[0][1] + timedelta(days=7)
                break
        else:
            date = dates[0][1]

        if date < datetime.now():
            date = date.replace(day=(datetime.now().day))
            if date < datetime.now():
                date = date + timedelta(days=1)

        x = re.search(r"([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]", dates[0][0])
        if x is None:
            date = date.replace(hour=9, minute=0, second=0)

        date_str = dates[0][0]

        return date, date_str

    async def get_embed(self, row, unverified_by):
        user = self.bot.get_user(row.user_id)
        if user is None:
            try:
                user = await self.bot.fetch_user(row.user_id)
            except discord.errors.NotFound:
                return
        if unverified_by != user:
            title = text.get("unverify", "unverified by")
        else:
            title = "Self unverify"

        reverify_on = row.end_time.strftime("%d.%m.%Y %H:%M")

        embed = self.create_embed(author=user, title=title, description=text.get("unverify", "unverified"))
        embed.add_field(name=text.get("unverify", "reverify on"), value=reverify_on, inline=True)
        if row.reason != "Self unverify":
            embed.add_field(name=text.get("unverify", "reason title"), value=row.reason, inline=False)

        return embed, user

    async def reverify_user(self, row, time=None):
        user = self.bot.get_user(row.user_id)
        if user is None:
            try:
                user = await self.bot.fetch_user(row.user_id)
            except discord.errors.NotFound:
                return

        if time is not None:
            await asyncio.sleep(time)
        await self.log(level="info", message=f"Reverifying {user.name}")
        # TODO await user.send(embed=embed)
        repository.set_finished(row.idx)

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command(
        brief=text.get("unverify", "selfunverify desc"),  # TODO fix
        description=text.get("unverify", "selfunverify desc"),  # TODO fix
        help=text.fill("unverify", "selfunverify help", prefix=config.prefix),  # TODO fix
    )
    async def selfunverify(self, ctx):
        message = ctx.message
        lines = message.content.split("\n")
        arg = lines.pop(0)
        arg = arg.replace("weekend", "saturday")
        date, date_str = await self.parse_datetime(arg)

        if date is None:
            if len(lines) == 0:
                await ctx.send(">>> " + text.fill("unverify", "selfunverify help", prefix=config.prefix))
                return
            await ctx.send(text.get("unverify", "datetime not found"))
            date = datetime.now() + timedelta(days=1)

        for prefix in config.prefixes:
            if arg[0] == prefix:
                arg = arg.replace(f"{prefix}selfunverify ", "")

        arg = arg.replace(date_str, "")
        args = re.split("[;, \n]", arg)
        while "" in args:
            args.remove("")
        roles_to_keep = []

        for value in args:
            role = discord.utils.get(ctx.guild.roles, name=value)
            channel = discord.utils.get(ctx.guild.channels, name=value)
            if role is not None and role in ctx.message.author.roles:
                roles_to_keep.append(role)
            elif channel is not None:
                perms = channel.permissions_for(ctx.message.author)
                user_overw = channel.overwrites_for(ctx.message.author)

                if not perms.read_messages:
                    continue

                for role in ctx.message.author.roles:
                    overwrites = channel.overwrites_for(role)
                    if overwrites.read_messages and user_overw.read_messages is None:
                        user_overw.update(read_messages=True)
                        await channel.set_permissions(
                            ctx.message.author, overwrite=user_overw, reason="Unverify"
                        )
                        break

        lines = "\n".join(lines)
        if len(lines) > 1024:
            lines = lines[:1024]
            lines = lines[:-3] + "```" if lines.count("```") % 2 != 0 else lines

        return


def setup(bot):
    bot.add_cog(Unverify(bot))

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
from repository import remind_repo


repository = remind_repo.RemindRepository()


class Reminder(basecog.Basecog):
    """Voting based commands"""

    def __init__(self, bot):
        self.bot = bot
        self.remind_loop.start()

    def cog_unload(self):
        self.remind_loop.cancel()

    @tasks.loop(seconds=10.0)
    async def remind_loop(self):
        repo = repository.get_ordered()
        if repo != []:
            for row in repo:
                duration = row.new_date - datetime.now()
                duration_in_s = duration.total_seconds()
                if row.new_date < datetime.now():
                    await self.log(level="info", message="Remind loop - waiting until ready()")
                    await self.send_reminder(row)
                elif duration_in_s < 10:
                    await self.send_reminder(row, time=duration_in_s)

    @remind_loop.before_loop
    async def before_printer(self):
        await self.log(level="info", message="Remind loop - waiting until ready()")
        await self.bot.wait_until_ready()

    async def parse_datetime(self, arg):
        dates = search_dates(
            arg.replace(".", "-"),
            languages=["en"],
            settings={"PREFER_DATES_FROM": "future", "PREFER_DAY_OF_MONTH": "first", "DATE_ORDER": "DMY"},
        )
        if dates is None:
            return None

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

        return date

    async def send_reminder(self, row, time=None):
        user = self.bot.get_user(row.user_id)
        if user is None:
            try:
                user = await self.bot.fetch_user(row.user_id)
            except discord.errors.NotFound:
                return

        reminder_user = self.bot.get_user(row.reminder_user_id)
        if reminder_user is None:
            try:
                reminder_user = await self.bot.fetch_user(row.reminder_user_id)
                reminder_user_name = discord.utils.escape_markdown(reminder_user.display_name)
            except discord.errors.NotFound:
                reminder_user_name = "_(Unknown user)_"
        else:
            reminder_user_name = discord.utils.escape_markdown(reminder_user.display_name)

        embed = self.create_embed(author=reminder_user, title=text.get("remindme", "reminder"))
        if row.user_id != row.reminder_user_id:
            embed.add_field(name=text.get("remindme", "reminder by"), value=reminder_user_name, inline=True)
        if row.message != "":
            embed.add_field(name=text.get("remindme", "reminder message"), value=row.message, inline=False)
        embed.add_field(name=text.get("remindme", "reminder link"), value=row.permalink, inline=True)
        if time is not None:
            await asyncio.sleep(time)
        await user.send(embed=embed)
        repository.delete(row.idx)

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command(
        brief=text.get("remindme", "remindme desc"),
        description=text.get("remindme", "remindme desc"),
        help=text.fill("remindme", "remindme help", prefix=config.prefix),
    )
    async def remindme(self, ctx):
        message = ctx.message
        lines = message.content.split("\n")
        arg = lines.pop(0)
        arg = arg.replace("weekend", "saturday")
        date = await self.parse_datetime(arg)
        lines = "\n".join(lines)

        if len(lines) > 1024:
            lines = lines[:1024]
            lines = lines[:-3] + "```" if lines.count("```") % 2 != 0 else lines

        if date is None:
            if len(lines) == 0:
                await ctx.send(">>> " + text.fill("remindme", "remindme help", prefix=config.prefix))
                return
            await ctx.send(text.get("remindme", "datetime not found"))
            date = datetime.now() + timedelta(days=1)
        repository.add(
            user_id=ctx.author.id,
            reminder_user_id=ctx.author.id,
            permalink=ctx.message.jump_url,
            message=lines,
            origin_date=ctx.message.created_at,
            new_date=date,
        )
        date = date.strftime("%d.%m.%Y %H:%M")
        await ctx.message.add_reaction("✅")
        await ctx.message.author.send(text.fill("remindme", "reminder confirmation", name="tebe", date=date))
        return

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command(
        brief=text.get("remindme", "remind desc"),
        description=text.get("remindme", "remind desc"),
        help=text.fill("remindme", "remind help", prefix=config.prefix),
    )
    async def remind(self, ctx, member: discord.Member):
        message = ctx.message
        lines = message.content.split("\n")
        arg = lines.pop(0)
        arg = arg.replace("weekend", "saturday")
        date = await self.parse_datetime(arg)
        lines = "\n".join(lines)

        if len(lines) == 0:
            await ctx.send(">>> " + text.fill("remindme", "remind help", prefix=config.prefix))
            return
        elif len(lines) > 1024:
            lines = lines[:1024]

        if date is None:
            await ctx.send(text.get("remindme", "datetime not found"))
            date = datetime.now() + timedelta(days=1)
        repository.add(
            user_id=member.id,
            reminder_user_id=ctx.author.id,
            permalink=ctx.message.jump_url,
            message=lines,
            origin_date=ctx.message.created_at,
            new_date=date,
        )
        date = date.strftime("%d.%m.%Y %H:%M")
        await ctx.message.add_reaction("✅")
        await ctx.message.author.send(
            text.fill("remindme", "reminder confirmation", name=member.display_name, date=date)
        )
        return


def setup(bot):
    bot.add_cog(Reminder(bot))

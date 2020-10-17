import re
import asyncio
from datetime import datetime
from datetime import timedelta
from dateparser.search import search_dates

import discord
from discord.ext import tasks, commands

from core import check, basecog
from core.text import text
from core.config import config
from repository import remind_repo


repository = remind_repo.RemindRepository()


class Reminder(basecog.Basecog):
    """Voting based commands"""

    def __init__(self, bot):
        super().__init__(bot)
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
                if row.status in {"waiting", "postponed"}:
                    if row.new_date < datetime.now():
                        await self.send_reminder(row)
                    elif duration_in_s < 10:
                        await self.send_reminder(row, time=duration_in_s)
                elif row.status == "finished":
                    if row.new_date < (datetime.now() - timedelta(days=7)):
                        await self.log(
                            level="debug",
                            message=f"Deleting reminder from db: ID: {row.idx}, time: {row.new_date}, status: {row.status}, \n    message: {row.message}",
                        )
                        repository.delete(row.idx)

    @remind_loop.before_loop
    async def before_remind_loop(self):
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

        date_str = dates[0][0]

        return date, date_str

    async def get_embed(self, row):
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

        return embed, user

    async def send_reminder(self, row, time=None):
        embed, user = await self.get_embed(row)

        if time is not None:
            await asyncio.sleep(time)
        await self.log(level="info", message=f"Sending reminder to {user.name}")
        await user.send(embed=embed)
        repository.set_finished(row.idx)

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command(
        brief=text.get("remindme", "remindme desc"),
        description=text.get("remindme", "remindme desc"),
        help=text.fill("remindme", "remindme help", prefix=config.prefix),
    )
    async def remindme(self, ctx):
        message = ctx.message
        lines = message.content.split("\n")
        arg = lines[0]
        arg = arg.replace("weekend", "saturday")
        date, date_str = await self.parse_datetime(arg)

        lines = "\n".join(lines)
        for prefix in config.prefixes:
            if lines[0] == prefix:
                lines = lines.replace(f"{prefix}remindme ", "")

        lines = lines.replace(date_str, "")
        lines = re.split(" ", lines)
        while "" in lines:
            lines.remove("")
        lines = " ".join(lines)

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

        await self.log(level="debug", message=f"Reminder created for {ctx.author.name}")

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
        arg = lines[0]
        arg = arg.replace("weekend", "saturday")
        date, date_str = await self.parse_datetime(arg)

        lines = "\n".join(lines)
        for prefix in config.prefixes:
            if lines[0] == prefix:
                lines = lines.replace(f"{prefix}remind ", "")
        lines = lines.replace(f"<@!{member.id}>", "")

        lines = lines.replace(date_str, "")
        lines = re.split(" ", lines)
        while "" in lines:
            lines.remove("")
        lines = " ".join(lines)

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

        await self.log(level="debug", message=f"Reminder created for {ctx.author.name}")

        await ctx.message.add_reaction("✅")
        await ctx.message.author.send(
            text.fill("remindme", "reminder confirmation", name=member.display_name, date=date)
        )
        return

    @commands.group(pass_context=True)
    async def reminders(self, ctx):
        """Zobrazí upomínky uživatele"""
        if ctx.invoked_subcommand is None:
            repo = repository.get_user(user_id=ctx.author.id)
            if repo is None:
                await ctx.send(text.get("remindme", "no reminders for you"))
                return
            await self.reminder_list(ctx, repo)

    @commands.check(check.is_mod)
    @reminders.command(pass_context=True)
    async def all(self, ctx):
        """Zobrazí všechny upomínky"""
        repo = repository.get_ordered()
        if repo is None:
            await ctx.send(text.get("remindme", "no reminders"))
            return
        await self.reminder_list(ctx, repo)

    @commands.check(check.is_mod)
    @reminders.command(pass_context=True)
    async def finished(self, ctx):
        """Zobrazí dokončené upomínky"""
        repo = repository.get_finished()
        if repo is None:
            await ctx.send(text.get("remindme", "no reminders"))
            return
        await self.reminder_list(ctx, repo)

    async def reminder_list(self, ctx, repo):

        message = "```"
        for row in repo:
            date = row.new_date.strftime("%d.%m.%Y %H:%M")
            if row.message == "":
                msg_row = f"ID: {row.idx}, time: {date}, status: {row.status}\n"
            else:
                msg_row = f"ID: {row.idx}, time: {date}, status: {row.status}, \n    message: {row.message}\n"

            if len(message + msg_row + "```") > 2000:
                await ctx.send(str(message))
                message = "```"
            message += msg_row
        message = (message + "```") if message != "```" else "Žádné upomínky"

        await ctx.send(str(message))

    @commands.group(pass_context=True)
    async def reminder(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Zkus toto: `!help reminder`")

    @reminder.command(pass_context=True, aliases=["postpone", "delay"])
    async def reschedule(self, ctx, idx: int):
        """Přesune upomínku na jindy"""
        row = repository.get_idx(idx)
        if row == []:
            await ctx.send(text.get("remindme", "wrong ID"))
            return
        if row[0].user_id != ctx.author.id:
            await ctx.send(text.get("remindme", "cannot edit other's reminders"))
            return

        message = ctx.message.content
        message = message.replace("weekend", "saturday").replace(str(idx), "")
        date, date_str = await self.parse_datetime(message)
        print_date = date.strftime("%d.%m.%Y %H:%M")

        embed, user = await self.get_embed(row[0])
        embed.add_field(name=text.get("remindme", "reminder edit new time"), value=print_date, inline=False)
        embed.add_field(
            name=text.get("remindme", "reminder edit confirmation"),
            value=text.get("remindme", "reminder edit text"),
            inline=False,
        )

        user_id = user.id
        message = await ctx.send(embed=embed)
        await message.add_reaction("✅")
        await message.add_reaction("❎")
        while True:

            def chk(reaction, usr):
                return (
                    reaction.message.id == message.id
                    and (str(reaction.emoji) == "✅" or str(reaction.emoji) == "❎")
                    and usr.id == user_id
                )

            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", check=chk, timeout=config.delay_embed
                )
            except asyncio.TimeoutError:
                pass
            else:
                if str(reaction.emoji) == "✅":
                    await self.log(
                        level="debug",
                        message=f"Rescheduling reminder - ID: {row[0].idx}, time: {date}, status: {row[0].status}, \n    message: {row[0].message}",
                    )
                    repository.postpone(row[0].idx, date)
            try:
                await message.delete()
            except discord.errors.Forbidden:
                pass
            except discord.errors.NotFound:
                pass

    @reminder.command(pass_context=True, aliases=["remove"])
    async def delete(self, ctx, idx: int):
        """Smaže upomínku"""
        row = repository.get_idx(idx)
        if row == []:
            await ctx.send(text.get("remindme", "wrong ID"))
            return
        if row[0].user_id != ctx.author.id:
            await ctx.send(text.get("remindme", "cannot delete other's reminders"))
            return

        embed, user = await self.get_embed(row[0])
        embed.add_field(
            name=text.get("remindme", "reminder delete confirmation"),
            value=text.get("remindme", "reminder delete text"),
            inline=False,
        )
        user_id = user.id
        message = await ctx.send(embed=embed)
        await message.add_reaction("✅")
        await message.add_reaction("❎")
        while True:

            def chk(reaction, usr):
                return (
                    reaction.message.id == message.id
                    and (str(reaction.emoji) == "✅" or str(reaction.emoji) == "❎")
                    and usr.id == user_id
                )

            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", check=chk, timeout=config.delay_embed
                )
            except asyncio.TimeoutError:
                pass
            else:
                if str(reaction.emoji) == "✅":
                    await self.log(
                        level="debug",
                        message=f"Deleting reminder from db - ID: {row[0].idx}, time: {row[0].new_date}, status: {row[0].status}, \n    message: {row[0].message}",
                    )
                    repository.delete(row[0].idx)
            try:
                await message.delete()
            except discord.errors.Forbidden:
                pass
            except discord.errors.NotFound:
                pass


def setup(bot):
    bot.add_cog(Reminder(bot))

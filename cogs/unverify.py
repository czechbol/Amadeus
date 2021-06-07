import re
import asyncio
from datetime import datetime
from datetime import timedelta
from dateparser.search import search_dates

import discord
from discord import CategoryChannel
from discord.abc import PrivateChannel
from discord.ext import tasks, commands

from core import basecog, check
from core.text import text
from core.config import config
from repository import unverify_repo


repository = unverify_repo.UnverifyRepository()


class Unverify(basecog.Basecog):
    """Unverification based commands"""

    def __init__(self, bot):
        super().__init__(bot)
        self.unverify_loop.start()

    def cog_unload(self):
        self.unverify_loop.cancel()

    @tasks.loop(seconds=10.0)
    async def unverify_loop(self):
        repo = repository.get_unfinished()
        if repo != []:
            for row in repo:
                duration = row.end_time - datetime.now()
                duration_in_s = duration.total_seconds()
                if row.end_time < datetime.now():
                    await self.reverify_user(row)
                elif duration_in_s < 10:
                    await self.reverify_user(row, time=duration_in_s)

    @unverify_loop.before_loop
    async def before_unverify_loop(self):
        if not self.bot.is_ready():
            await self.log(
                level="info", message="Unverify loop - waiting until ready()"
            )
            await self.bot.wait_until_ready()

    async def parse_datetime(self, arg):
        dates = search_dates(
            arg.replace(".", "-"),
            languages=["en"],
            settings={
                "PREFER_DATES_FROM": "future",
                "PREFER_DAY_OF_MONTH": "first",
                "DATE_ORDER": "DMY",
            },
        )
        if dates is None:
            return None, ""

        weekdays = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]

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

        date_str = dates[0][0]

        return date, date_str

    async def reverify_user(self, row, time=None):
        guild = self.bot.get_guild(row.guild_id)
        if guild is None:
            return
        member = guild.get_member(row.user_id)
        if member is None:
            try:
                member = await guild.fetch_member(row.user_id)
            except discord.errors.NotFound:
                if row.status == "user left server":
                    return
                else:
                    await self.log(
                        level="info",
                        message=f"Couldn't find member with id: {row.user_id}",
                    )
                    repository.set_left_server(row.idx)
                    return
        if time is not None:
            await asyncio.sleep(time)
        await self.log(level="info", message=f"Reverifying {member.name}")
        roles = []
        for role_id in row.roles_to_return:
            role = discord.utils.get(guild.roles, id=role_id)
            roles.append(role)
        try:
            await member.add_roles(*roles, reason=None, atomic=True)
        except discord.errors.Forbidden:
            pass
        for channel_id in row.channels_to_return:
            channel = discord.utils.get(guild.channels, id=channel_id)
            user_overw = channel.overwrites_for(member)
            user_overw.update(read_messages=True)
            await channel.set_permissions(
                member, overwrite=user_overw, reason="Reverify"
            )

        for channel_id in row.channels_to_remove:
            channel = discord.utils.get(guild.channels, id=channel_id)
            user_overw = channel.overwrites_for(member)
            user_overw.update(read_messages=None)
            await channel.set_permissions(
                member, overwrite=user_overw, reason="Reverify"
            )

        for id in config.roles_unverify:
            role = discord.utils.get(guild.roles, id=id)
            if role is not None:
                unverify_role = role
                try:
                    await member.remove_roles(
                        unverify_role, reason="Reverify", atomic=True
                    )
                except discord.errors.Forbidden:
                    pass
                break
            else:
                return None

        await self.log(
            level="info", message=f"Reverify success for member {member.name}"
        )
        try:
            await member.send(
                text.fill("unverify", "reverified", guild_name=guild.name)
            )
        except discord.Forbidden:
            await self.log(
                level="info",
                message=f"Couldn't send reverify info to {member.name}'s DM",
            )

        repository.set_finished(row.idx)

    async def unverify_user(
        self,
        ctx: commands.Context,
        member: discord.abc.User,
        lines: str,
        date: datetime,
        func: str,
        args: str = "",
    ):
        if isinstance(ctx.channel, PrivateChannel):
            guild = self.getGuild()
            member = guild.get_member(member.id)
        else:
            guild = ctx.guild
        roles_to_keep = []
        roles_to_remove = []
        channels_to_keep = []
        removed_channels = []

        for id in config.roles_unverify:
            role = discord.utils.get(guild.roles, id=id)
            if role is not None:
                unverify_role = role
                break
            else:
                return None

        for value in args:
            role = discord.utils.get(guild.roles, name=value)
            channel = discord.utils.get(guild.channels, name=value)
            if role is not None and role in member.roles:
                roles_to_keep.append(role)
            elif channel is not None:
                perms = channel.permissions_for(member)

                if not perms.read_messages:
                    continue
                channels_to_keep.append(channel)

        for role in member.roles:
            if role not in roles_to_keep and role.position != 0:
                roles_to_remove.append(role)
        try:
            await member.remove_roles(*roles_to_remove, reason=func, atomic=True)
        except discord.errors.Forbidden:
            pass
        await member.add_roles(unverify_role, reason=func, atomic=True)
        await asyncio.sleep(2)

        for channel in member.guild.channels:
            if not isinstance(channel, CategoryChannel):
                perms = channel.permissions_for(member)
                user_overw = channel.overwrites_for(member)

                if channel in channels_to_keep:
                    if not perms.read_messages:
                        user_overw.update(read_messages=True)
                        await channel.set_permissions(
                            member, overwrite=user_overw, reason=func
                        )
                elif perms.read_messages and not user_overw.read_messages:
                    pass
                elif not perms.read_messages:
                    pass
                else:
                    user_overw.update(read_messages=False)
                    await channel.set_permissions(
                        member, overwrite=user_overw, reason=func
                    )
                    removed_channels.append(channel.id)

        removed_roles = [role.id for role in roles_to_remove]
        added_channels = [channel.id for channel in channels_to_keep]

        if len(lines) > 1024:
            lines = lines[:1024]
            lines = lines[:-3] + "```" if lines.count("```") % 2 != 0 else lines

        result = repository.add(
            guild_id=member.guild.id,
            user_id=member.id,
            start_time=datetime.now(),
            end_time=date,
            roles_to_return=removed_roles,
            channels_to_return=removed_channels,
            channels_to_remove=added_channels,
            reason=lines,
            typ=func,
        )
        return result

    @commands.check(check.is_elevated)
    @commands.command(
        brief=text.get("unverify", "unverify desc"),
        description=text.get("unverify", "unverify desc"),
        help=text.fill("unverify", "unverify help", prefix=config.prefix),
    )
    async def unverify(self, ctx, member: discord.Member):
        message = ctx.message
        lines = message.content.split("\n")
        arg = lines[0]
        arg = arg.replace("weekend", "saturday")
        date, date_str = await self.parse_datetime(arg)
        await self.log(
            level="info", message=f"Unverify: Member - {member.name}, Until - {date}"
        )

        if isinstance(ctx.channel, PrivateChannel):
            guild = self.getGuild()
            member = guild.get_member(member.id)
        else:
            guild = ctx.guild

        if date is None:
            if len(lines) == 0:
                await ctx.send(
                    ">>> "
                    + text.fill("unverify", "unverify help", prefix=config.prefix)
                )
                return
            await ctx.send(text.get("unverify", "datetime not found"))
            date = datetime.now() + timedelta(days=1)
        printdate = date.strftime("%d.%m.%Y %H:%M")

        lines = "\n".join(lines)
        for prefix in config.prefixes:
            if lines[0] == prefix:
                lines = lines.replace(f"{prefix}unverify ", "")

        lines = lines.replace(f"<@!{member.id}>", "")

        if len(lines) > 1024:
            lines = lines[:1024]
            lines = lines[:-3] + "```" if lines.count("```") % 2 != 0 else lines
        lines = lines if not lines == "" else "Unverify"

        lines = lines.replace(date_str, "")
        lines = re.split(" ", lines)
        while "" in lines:
            lines.remove("")
        lines = " ".join(lines)

        result = await self.unverify_user(
            ctx, member=member, lines=lines, date=date, func="Unverify"
        )

        if result is not None:
            await self.log(
                level="debug",
                message=f"Unverify success: Member - {member.name}, Until - {date}, ID - {result.idx}",
            )

            embed = self.create_embed(
                author=ctx.message.author,
                title=text.fill("unverify", "unverified", guild_name=guild.name),
            )
            embed.add_field(
                name=text.get("unverify", "reverify on"), value=printdate, inline=False
            )
            if lines != "":
                embed.add_field(
                    name=text.get("unverify", "reason title"), value=lines, inline=False
                )
            try:
                await member.send(embed=embed)
                await ctx.send(
                    f"Uživateli {member.name} byla dočasně odebrána práva na server.\nNavrácena budou: {printdate}"
                )
            except discord.Forbidden:
                await ctx.send(
                    f"Uživateli {member.name} byla dočasně odebrána práva na server.\nNavrácena budou: {printdate}\nNebylo možné odeslat uživateli informační zprávu."
                )

        else:
            await self.log(
                level="debug",
                message=f"Unverify failed: Member - {member.name} already unverified.",
            )

    @commands.cooldown(rate=1, per=3600.0, type=commands.BucketType.user)
    @commands.command(
        brief=text.get("unverify", "selfunverify desc"),
        description=text.get("unverify", "selfunverify desc"),
        help=text.fill("unverify", "selfunverify help", prefix=config.prefix),
    )
    async def selfunverify(self, ctx):
        message = ctx.message
        lines = message.content.split("\n")
        arg = lines.pop(0)
        arg = arg.replace("weekend", "saturday")
        date, date_str = await self.parse_datetime(arg)
        member = ctx.message.author
        await self.log(
            level="info",
            message=f"Selfunverify: Member - {member.name}, Until - {date}",
        )
        if isinstance(ctx.channel, PrivateChannel):
            guild = self.getGuild()
            member = guild.get_member(member.id)
        else:
            guild = ctx.guild

        if date is None:
            if len(lines) == 0:
                await ctx.send(
                    ">>> "
                    + text.fill("unverify", "selfunverify help", prefix=config.prefix)
                )
                return
            await ctx.send(text.get("unverify", "datetime not found"))
            date = datetime.now() + timedelta(days=1)
        printdate = date.strftime("%d.%m.%Y %H:%M:%S")

        for prefix in config.prefixes:
            if arg[0] == prefix:
                arg = arg.replace(f"{prefix}selfunverify ", "")

        arg = arg.replace(date_str, "")
        args = re.split("[;, \n]", arg)
        while "" in args:
            args.remove("")

        result = await self.unverify_user(
            ctx, member=member, args=args, lines=lines, date=date, func="Self unverify"
        )

        if result is not None:
            await self.log(
                level="debug",
                message=f"Selfunverify success: Member - {member.name}, Until - {date}",
            )
            embed = self.create_embed(
                author=ctx.message.author,
                title=text.fill("unverify", "unverified", guild_name=guild.name),
            )
            embed.add_field(
                name=text.get("unverify", "reverify on"), value=printdate, inline=False
            )
            try:
                await member.send(embed=embed)
                await ctx.send(
                    f"Uživateli {member.name} byla dočasně odebrána práva na server.\nNavrácena budou: {printdate}"
                )
            except discord.Forbidden:
                await ctx.send(
                    f"Uživateli {member.name} byla dočasně odebrána práva na server.\nNavrácena budou: {printdate}\nNebylo možné odeslat uživateli informační zprávu."
                )

        else:
            await self.log(
                level="debug",
                message=f"Selfunverify failed: Member - {member.name} already unverified.",
            )

    @commands.check(check.is_elevated)
    @commands.group(pass_context=True)
    async def unverifies(self, ctx):
        if ctx.invoked_subcommand is None:
            repo_all = repository.get_ordered()
            repo_self = repository.get_selfunverify()
            repo = repository.get_unverify()
            embed = self.create_embed(author=ctx.message.author, title="Unverify count")
            embed.add_field(
                name="Active Self unverify", value=str(len(repo_self)), inline=True
            )
            embed.add_field(name="Active Unverify", value=str(len(repo)), inline=True)
            embed.add_field(
                name="All in history", value=str(len(repo_all)), inline=True
            )
            await ctx.send(embed=embed)

    @commands.command(
        brief=text.get("unverify", "gn desc"),
        description=text.get("unverify", "gn desc"),
        help=text.fill("unverify", "gn help", prefix=config.prefix),
    )
    async def gn(self, ctx):
        member = ctx.message.author
        date, date_str = await self.parse_datetime("06:00")
        lines = "gn"
        await self.log(
            level="info", message=f"Unverify: Member - {member.name}, Until - {date}"
        )

        if isinstance(ctx.channel, PrivateChannel):
            guild = self.getGuild()
            member = guild.get_member(member.id)
        else:
            guild = ctx.guild

        if date is None:
            await ctx.send(
                "Could not do that because Czechbol is lazy and didn't create me properly."
            )
            return
        printdate = date.strftime("%d.%m.%Y %H:%M")

        result = await self.unverify_user(
            ctx, member=member, lines=lines, date=date, func="Unverify"
        )

        if result is not None:
            await self.log(
                level="debug",
                message=f"Unverify success: Member - {member.name}, Until - {date}",
            )

            embed = self.create_embed(
                author=ctx.message.author,
                title=text.get("unverify", "gm"),
            )
            embed.add_field(
                name=text.get("unverify", "reverify on"), value=printdate, inline=False
            )
            if lines != "":
                embed.add_field(
                    name=text.get("unverify", "reason title"),
                    value="Goodnight příkaz",
                    inline=False,
                )
            embed.add_field(
                name=text.get("unverify", "gm return title"),
                value=text.get("unverify", "gm return"),
                inline=False,
            )
            try:
                await member.send(embed=embed)
                await ctx.send(
                    f"Uživateli {member.name} byla dočasně odebrána práva na server.\nNavrácena budou: {printdate}"
                )
            except discord.Forbidden:
                await ctx.send(
                    f"Uživateli {member.name} byla dočasně odebrána práva na server.\nNavrácena budou: {printdate}\nNebylo možné odeslat uživateli informační zprávu."
                )

            await ctx.send(f"Dobrou noc, {member.name}!")
        else:
            await self.log(
                level="debug",
                message=f"Unverify failed: Member - {member.name} already unverified.",
            )

    @unverifies.command(pass_context=True)
    async def all(self, ctx):

        repo = repository.get_ordered()

        if repo != []:
            embeds = await self.unverify_embeds(ctx, repo)
            await self.unverify_pages(ctx, embeds)
            return
        await ctx.send("No unverifies found.")
        return

    @unverifies.command(pass_context=True)
    async def waiting(self, ctx):

        repo = repository.get_waiting()

        if repo != []:
            embeds = await self.unverify_embeds(ctx, repo)
            await self.unverify_pages(ctx, embeds)
            return
        await ctx.send("No unverifies found.")
        return

    async def unverify_embeds(self, ctx, repo):
        embed_list = []

        for idx, row in enumerate(repo, start=1):
            user = self.bot.get_user(row.user_id)
            guild = self.bot.get_guild(row.guild_id)
            if user is None:
                try:
                    user = await self.bot.fetch_user(row.user_id)
                    user_name = discord.utils.escape_markdown(user.display_name)
                except discord.errors.NotFound:
                    user_name = "_(Unknown user)_"
            else:
                user_name = discord.utils.escape_markdown(user.display_name)

            start_time = row.start_time.strftime("%d.%m.%Y %H:%M")
            end_time = row.end_time.strftime("%d.%m.%Y %H:%M")

            roles = []
            for role_id in row.roles_to_return:
                role = discord.utils.get(guild.roles, id=role_id)
                roles.append(role)
            channels = []
            for channel_id in row.channels_to_return:
                channel = discord.utils.get(guild.channels, id=channel_id)
                channels.append(channel)

            embed = self.create_embed(author=ctx.message.author, title="Unverify list")
            embed.add_field(name="User", value=user_name, inline=False)
            embed.add_field(name="Start time", value=str(start_time), inline=True)
            embed.add_field(name="End time", value=str(end_time), inline=True)
            embed.add_field(name="Unverify ID", value=row.idx, inline=True)
            embed.add_field(name="Status", value=row.status, inline=True)
            if roles != []:
                embed.add_field(
                    name="Roles to return",
                    value=", ".join(role.name for role in roles),
                    inline=True,
                )

            if channels != []:
                embed.add_field(
                    name="Channels to return",
                    value=", ".join(channel.name for channel in channels),
                    inline=True,
                )
            if row.reason != "{}":
                embed.add_field(name="Reason", value=row.reason, inline=False)
            embed.add_field(name="Type", value=row.typ, inline=False)
            embed.add_field(
                name="Page",
                value="{curr}/{total}".format(curr=idx, total=len(repo)),
                inline=False,
            )
            embed_list.append(embed)
        return embed_list

    async def unverify_pages(self, ctx, embeds):
        message = await ctx.send(embed=embeds[0])
        pagenum = 0
        await message.add_reaction("◀️")
        await message.add_reaction("▶️")
        while True:

            def check(reaction, user):
                return (
                    reaction.message.id == message.id
                    and (str(reaction.emoji) == "◀️" or str(reaction.emoji) == "▶️")
                    and not user == self.bot.user
                )

            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", check=check, timeout=300.0
                )
            except asyncio.TimeoutError:
                break
            else:
                if str(reaction.emoji) == "◀️":
                    pagenum -= 1
                    if pagenum < 0:
                        pagenum = len(embeds) - 1
                    try:
                        await message.remove_reaction("◀️", user)
                    except discord.errors.Forbidden:
                        pass
                    await message.edit(embed=embeds[pagenum])
                if str(reaction.emoji) == "▶️":
                    pagenum += 1
                    if pagenum >= len(embeds):
                        pagenum = 0
                    try:
                        await message.remove_reaction("▶️", user)
                    except discord.errors.Forbidden:
                        pass
                    await message.edit(embed=embeds[pagenum])

    @commands.check(check.is_elevated)
    @commands.command()
    async def reverify(self, ctx, idx: int):
        repo = repository.get_idx(idx)
        if repo != [] and repo[0].status == "waiting":
            row = repo[0]
            user = self.bot.get_user(row.user_id)
            if user is None:
                try:
                    user = await self.bot.fetch_user(row.user_id)
                    user_name = discord.utils.escape_markdown(user.display_name)
                except discord.errors.NotFound:
                    user_name = "_(Unknown user)_"
            else:
                user_name = discord.utils.escape_markdown(user.display_name)
            await self.reverify_user(row)
            await ctx.send(f"Reverified {user_name}")
        else:
            await ctx.send("ID not found or already finished.")

    @commands.command()
    async def gm(self, ctx):
        member = ctx.message.author
        repo = repository.get_user(member.id)
        for rep in repo:
            if rep != [] and rep.status == "waiting":
                if rep.reason == "gn":
                    user = self.bot.get_user(rep.user_id)
                    if user is None:
                        try:
                            user = await self.bot.fetch_user(rep.user_id)
                            user_name = discord.utils.escape_markdown(user.display_name)
                        except discord.errors.NotFound:
                            user_name = "_(Unknown user)_"
                    else:
                        user_name = discord.utils.escape_markdown(user.display_name)
                    await self.reverify_user(rep)
                    await ctx.send(f"Reverified {user_name}")
                else:
                    await ctx.send("Forbidden")
                break
        else:
            await ctx.send("ID not found or already finished.")


def setup(bot):
    bot.add_cog(Unverify(bot))

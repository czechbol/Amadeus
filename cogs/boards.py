import asyncio

import discord
from discord import CategoryChannel, VoiceChannel
from discord.ext import commands
from discord.abc import PrivateChannel

from core import basecog
from core.text import text
from core.config import config
from repository import user_channel_repo


repository = user_channel_repo.UserChannelRepository()


class Boards(basecog.Basecog):
    """Commands for leaderboards"""

    def __init__(self, bot):
        self.bot = bot
        self.handled = []

    async def get_history(self, channel, after):
        if after is None:
            messages = await channel.history(limit=None, oldest_first=True).flatten()
        else:
            messages = await channel.history(limit=None, after=after, oldest_first=True).flatten()
        return messages

    async def add_to_db(self, msg):
        repository.increment(
            channel_id=msg.channel.id,
            user_id=msg.author.id,
            guild_id=msg.guild.id,
            last_message_at=msg.created_at,
            last_message_id=msg.id,
        )
        return

    async def msg_iter(self, messages):
        for idx, msg in enumerate(messages):
            if idx % 2500 == 0:
                await asyncio.sleep(2)
            await self.add_to_db(msg)
        return

    async def sort_channels(self, lis, all_allowed):
        results = []
        for ch in lis:
            if all_allowed is True or (
                ch["channel_id"] not in config.board_ignored_channels
                and ch["user_id"] not in config.board_ignored_users
            ):

                for row in results:
                    if row["channel_id"] == ch["channel_id"] and row["guild_id"] == ch["guild_id"]:
                        row["count"] += ch["count"]
                        if row["last_message_at"] < ch["last_message_at"]:
                            row["last_message_at"] = ch["last_message_at"]
                            row["last_message_id"] = ch["last_message_id"]
                        break
                else:
                    results.append(
                        {
                            "channel_id": ch["channel_id"],
                            "guild_id": ch["guild_id"],
                            "count": ch["count"],
                            "last_message_at": ch["last_message_at"],
                            "last_message_id": ch["last_message_id"],
                        }
                    )
        results = sorted(results, key=lambda i: (i["count"]), reverse=True)
        return results

    async def sort_userchannel(self, lis):
        results = []
        for ch in lis:
            for row in results:
                if (
                    row["channel_id"] == ch["channel_id"]
                    and row["guild_id"] == ch["guild_id"]
                    and row["user_id"] == ch["user_id"]
                ):
                    row["count"] += ch["count"]
                    if row["last_message_at"] < ch["last_message_at"]:
                        row["last_message_at"] = ch["last_message_at"]
                    break
            else:
                results.append(
                    {
                        "channel_id": ch["channel_id"],
                        "guild_id": ch["guild_id"],
                        "user_id": ch["user_id"],
                        "count": ch["count"],
                        "last_message_at": ch["last_message_at"],
                    }
                )
        results = sorted(results, key=lambda i: (i["count"]), reverse=True)
        return results

    async def sort_users(self, lis, all_allowed):
        results = []
        for ch in lis:
            if all_allowed is True or (
                ch["channel_id"] not in config.board_ignored_channels
                and ch["user_id"] not in config.board_ignored_users
            ):
                for row in results:
                    if row["user_id"] == ch["user_id"]:
                        row["count"] += ch["count"]
                        if row["last_message_at"] < ch["last_message_at"]:
                            row["last_message_at"] = ch["last_message_at"]
                        break
                else:
                    results.append(
                        {
                            "user_id": ch["user_id"],
                            "count": ch["count"],
                            "last_message_at": ch["last_message_at"],
                        }
                    )
        results = sorted(results, key=lambda i: (i["count"]), reverse=True)
        return results

    @commands.cooldown(rate=3, per=120.0, type=commands.BucketType.user)
    @commands.command(description=text.get("boards", "channel board"))
    async def channelboard(self, ctx, offset: int = 0):
        await asyncio.sleep(0.1)
        user_channels = repository.get_user_channels()

        if not user_channels:
            return ctx.send(text.get("boards", "not found"))

        results = await self.sort_channels(user_channels, False)

        offset -= 1  # convert to be zero-indexed

        if offset > len(results):
            return await ctx.send(text.get("boards", "offset too big"))

        boards, pagenum = await self.boards_generator(ctx, results, offset, "channel")

        await self.board_pages(ctx, boards, pagenum)

        return

    @commands.cooldown(rate=3, per=120.0, type=commands.BucketType.user)
    @commands.command(description=text.get("boards", "user board"))
    async def userboard(self, ctx, offset: int = 0):
        await asyncio.sleep(0.1)
        user_channels = repository.get_user_channels()

        if not user_channels:
            return ctx.send(text.get("boards", "not found"))

        results = await self.sort_users(user_channels, False)

        offset -= 1  # convert to be zero-indexed

        if offset > len(results):
            return await ctx.send(text.get("boards", "offset too big"))

        boards, pagenum = await self.boards_generator(ctx, results, offset, "user")

        await self.board_pages(ctx, boards, pagenum)

        return

    @commands.cooldown(rate=3, per=120.0, type=commands.BucketType.user)
    @commands.command()
    async def stalk(self, ctx, member: discord.Member):
        await asyncio.sleep(0.1)
        user_channels = repository.get_user_channels()

        if not user_channels:
            return await ctx.send(text.get("boards", "not found"))

        results = await self.sort_users(user_channels, False)
        for idx, result in enumerate(results):
            if member.id == result["user_id"]:
                offset = idx
                print(offset)
                break
        else:
            return await ctx.send(text.get("boards", "not found"))

        boards, pagenum = await self.boards_generator(ctx, results, offset, "stalk")

        await self.board_pages(ctx, boards, pagenum)

        return

    async def boards_generator(self, ctx, results, offset, typ):
        # splits results into config.board_top sized chunks (chunks = list of lists)
        chunks = [results[i : i + config.board_top] for i in range(0, len(results), config.board_top)]

        boards = []
        # Iterates through chunks to get pages
        for idx, chunk in enumerate(chunks):
            chunk_position = idx * config.board_top

            embed = discord.Embed(
                title=text.get("boards", typ + " board title"),
                description=text.get("boards", typ + " board desc"),
                color=config.color,
            )

            pagenum = 0  # index of board page to show first
            lines = []
            author_position = -1
            # Iterates through channels in chunk to get lines of a single board
            for pos, item in enumerate(chunk):
                position = chunk_position + pos  # item position among all items

                index = f"{position + 1:>2}"
                count = f"{item['count']:>5}"
                if typ == "channel":
                    channel = self.bot.get_channel(item["channel_id"])
                    name = "#{}".format(channel.name)
                else:
                    user = self.bot.get_user(item["user_id"])
                    if user is None:
                        try:
                            user = await self.bot.fetch_user(item["user_id"])
                        except discord.errors.NotFound:
                            print(item["user_id"])
                            user_name = "_(Unknown user)_"
                    else:
                        user_name = user.display_name
                    name = "{}".format(user_name)
                    if user == ctx.author:  # displays author in bold, saves author position
                        author_position = position
                        name = "**" + name + "**"

                if position == offset:  # displays offset user/channel in bold, saves page number
                    pagenum = idx
                    name = "**" + name + "**"
                if typ == "channel" and (
                    isinstance(ctx.channel, PrivateChannel) or channel.guild.id != ctx.guild.id
                ):
                    # only shows channel guild if message didn't come from guild or message guild is different than board channel's guild
                    guild = discord.utils.escape_markdown(channel.guild.name)
                    lines.append(
                        text.fill(
                            "boards", "template guild", index=index, count=count, name=name, guild=guild,
                        )
                    )
                else:
                    lines.append(text.fill("boards", "template", index=index, count=count, name=name,))

            title = "top number" if idx == 0 else "top offset"

            embed.add_field(
                name=text.fill("boards", title, top=config.board_top, offset=(idx * config.board_top) + 1),
                value="\n".join(lines),
                inline=False,
            )

            # adds the YOUR POSITION field for userboard
            if typ == "user" and chunk_position < author_position < chunk_position + config.board_top:
                lines = []
                range_floor = author_position - config.board_around
                range_ceiling = author_position + config.board_around + 1
                print(author_position)
                print()
                for position in range(range_floor, range_ceiling):

                    print(position)

                    # do not wrap around (if the 'around' number is too high)
                    if position < 0:
                        continue

                    # get user object
                    item = results[position]
                    user = self.bot.get_user(item["user_id"])
                    if user is None:
                        try:
                            user = await self.bot.fetch_user(item["user_id"])
                        except discord.errors.NotFound:
                            user_name = "_(Unknown user)_"
                    else:
                        user_name = user.display_name

                    # get position string
                    index = f"{position + 1:>2}"
                    count = f"{item['count']:>5}"
                    user = self.bot.get_user(item["user_id"])
                    name = "{}".format(user_name)
                    if position == author_position:
                        name = "**" + name + "**"

                    lines.append(text.fill("boards", "template", index=index, name=name, count=count,))

                if len(lines) > 0:
                    embed.add_field(
                        name=text.get("boards", "author position"), value="\n".join(lines), inline=False,
                    )

            boards.append(embed)

        return boards, pagenum

    async def board_pages(self, ctx, boards, pagenum):
        msg = await ctx.send(embed=boards[pagenum])
        await msg.add_reaction("◀️")
        await msg.add_reaction("▶️")
        while True:

            def check(reaction, user):
                return (
                    reaction.message.id == msg.id
                    and (str(reaction.emoji) == "◀️" or str(reaction.emoji) == "▶️")
                    and not user == self.bot.user
                )

            try:
                reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=300.0)
            except asyncio.TimeoutError:
                try:
                    await msg.clear_reaction("◀️")
                    await msg.clear_reaction("▶️")
                except discord.errors.Forbidden:
                    pass
                break
            else:
                if pagenum > 0 and str(reaction.emoji) == "◀️":
                    pagenum -= 1
                    try:
                        await msg.remove_reaction("◀️", user)
                    except discord.errors.Forbidden:
                        pass
                    await msg.edit(embed=boards[pagenum])
                if pagenum < (len(boards) - 1) and str(reaction.emoji) == "▶️":
                    pagenum += 1
                    try:
                        await msg.remove_reaction("▶️", user)
                    except discord.errors.Forbidden:
                        pass
                    await msg.edit(embed=boards[pagenum])

    @commands.Cog.listener()
    async def on_message(self, message):
        if (
            not isinstance(message.channel, PrivateChannel)
            and not isinstance(message.channel, VoiceChannel)
            and not isinstance(message.channel, CategoryChannel)
        ):
            await self.add_to_db(message)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if (
            not isinstance(message.channel, PrivateChannel)
            and not isinstance(message.channel, VoiceChannel)
            and not isinstance(message.channel, CategoryChannel)
        ):
            channel_id = message.channel.id
            user_id = message.author.id
            guild_id = message.guild.id
            last_message_at = message.created_at
            last_message_id = message.id
            repository.decrement(
                channel_id=channel_id,
                user_id=user_id,
                guild_id=guild_id,
                last_message_at=last_message_at,
                last_message_id=last_message_id,
            )

    @commands.Cog.listener()
    async def on_ready(self):
        channels = repository.get_user_channels()
        results = None
        tasks = []
        admin = self.bot.get_user(config.admin_id)

        async with admin.typing():

            if channels is not None:
                results = await self.sort_channels(channels, True)

            for guild in self.bot.guilds:
                for channel in guild.channels:

                    if (
                        not isinstance(channel, PrivateChannel)
                        and not isinstance(channel, VoiceChannel)
                        and not isinstance(channel, CategoryChannel)
                    ):

                        if results is None:
                            messages = await self.get_history(channel, None)
                        else:
                            for res in results:
                                if res["channel_id"] == channel.id:
                                    after = res["last_message_at"]
                                    messages = await self.get_history(channel, after)
                                    break
                            else:
                                # try:
                                messages = await self.get_history(channel, None)
                                """except discord.errors.Forbidden:
                                    print(
                                        "Forbidden getting history for channel {channel} in guild {guild}".format(
                                            channel=channel, guild=guild.name
                                        )
                                    )
                                    continue"""  # TODO log this

                        if len(messages) > 0:
                            tasks.append(self.msg_iter(messages))

        for task in tasks:
            await task

        await admin.send(text.get("boards", "synced"))


def setup(bot):
    bot.add_cog(Boards(bot))

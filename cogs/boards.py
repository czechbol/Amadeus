import asyncio

import discord
from discord import CategoryChannel, VoiceChannel
from discord.ext import commands
from discord.abc import PrivateChannel

from core import basecog, check
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
    async def channelboard(self, ctx, offset: int = 1):
        await asyncio.sleep(0.5)
        user_channels = repository.get_user_channels()

        if not user_channels:
            return ctx.send(text.get("boards", "not found"))

        # convert to be zero-indexed
        offset -= 1
        if offset < 0:
            return await ctx.send(text.get("boards", "invalid offset"))

        results = await self.sort_channels(user_channels, False)

        if offset > len(results):
            return await ctx.send(text.get("boards", "offset too big"))

        embed = discord.Embed(
            title=text.get("boards", "channel board title"),
            description=text.get("boards", "channel board desc"),
            color=config.color,
        )

        # get data for "TOP X" list
        lines = []
        for position, item in enumerate(results):
            if position < offset:
                continue

            if position - offset >= config.board_top:
                break

            channel = self.bot.get_channel(item["channel_id"])
            if not hasattr(channel, "name"):
                # channel was not found
                continue

            # fmt: off
            if ctx.guild is not None and channel.guild.id == ctx.guild.id:
                lines.append(text.fill("boards", "channel template",
                    index=f"{position + 1:>2}",
                    count=f"{item['count']:>5}",
                    name=discord.utils.escape_markdown(channel.name)))
            else:
                # channel is on some other guild
                lines.append(text.fill("boards", "channel template guild",
                    index=f"{position + 1:>2}",
                    count=f"{item['count']:>5}",
                    name=discord.utils.escape_markdown(channel.name),
                    guild=discord.utils.escape_markdown(channel.guild.name)))
            # fmt: on
        title = "top number" if offset == 0 else "top offset"
        # fmt: off
        embed.add_field(
            name=text.fill("boards", title, top=config.board_top, offset=offset + 1),
            value="\n".join(lines),
            inline=False,
        )
        # fmt: on
        await ctx.send(embed=embed)

    @commands.cooldown(rate=3, per=120.0, type=commands.BucketType.user)
    @commands.command(description=text.get("boards", "user board"))
    async def userboard(self, ctx, offset: int = 1):
        await asyncio.sleep(0.5)
        user_channels = repository.get_user_channels()
        if not user_channels:
            return ctx.send(text.get("boards", "not found"))

        # convert to be zero-indexed
        offset -= 1
        if offset < 0:
            return await ctx.send(text.get("boards", "invalid offset"))

        users = await self.sort_users(user_channels, False)

        if offset > len(users):
            return await ctx.send(text.get("boards", "offset too big"))

        await self.sendUserboard(ctx, users, ctx.author, offset)

    @commands.cooldown(rate=3, per=120.0, type=commands.BucketType.user)
    @commands.command()
    async def stalk(self, ctx, member: discord.Member):
        await asyncio.sleep(0.5)
        user_channels = repository.get_user_channels()
        if not user_channels:
            return ctx.send(text.get("boards", "not found"))

        users = await self.sort_users(user_channels, False)

        offset = -1
        for position, item in enumerate(users):
            if item["user_id"] == member.id:
                offset = position
                break

        if offset < 0:
            return await ctx.send(text.get("boards", "not found"))

        if offset < config.board_top - config.board_around:
            offset = 0

        if offset > len(users):
            return await ctx.send(text.get("boards", "offset too big"))

        await self.sendUserboard(ctx, users, member, offset=0)

    async def sendUserboard(self, ctx, users, member: discord.Member, offset: int):
        # note: this offset is zero-indexed here, not like in userboard()
        # create an embed
        embed = discord.Embed(
            title=text.get("boards", "user board title"),
            description=text.get("boards", "user board desc"),
            color=config.color,
        )

        # get data for "TOP X" list
        lines = []
        author_position = -1
        for position, item in enumerate(users):
            if ctx.author.id == item["user_id"]:
                author_position = position

            if position < offset or position - offset >= config.board_top:
                continue

            # get user object
            user = self.bot.get_user(item["user_id"])
            if not hasattr(user, "display_name"):
                # user was not found
                continue

            user_name = discord.utils.escape_mentions(user.display_name)

            # get position string
            # fmt: off
            if item["user_id"] == member.id:
                user_position = position
                lines.append(text.fill("boards", "target template",
                    index=f"{position+1:>2}", name=user_name, count=f"{item['count']:>5}"))
            else:
                lines.append(text.fill("boards", "user template",
                    index=f"{position+1:>2}", name=user_name, count=f"{item['count']:>5}"))
            # fmt: on

        title = "top number" if offset == 0 else "top offset"
        embed.add_field(
            name=text.fill("boards", title, top=config.board_top, offset=offset + 1),
            value="\n".join(lines),
            inline=False,
        )

        # get data for "YOUR POSITION" list
        positions = [
            x + author_position for x in [y - config.board_around for y in range(config.board_around * 2)]
        ]
        lines = []
        for position in positions:
            # do not display "YOUR POSITION" if user is in "TOP X" and OFFSET is not set
            if offset == 0 and user_position < config.board_top - config.board_around:
                break

            # do not wrap around (if the 'around' number is too high)
            if position < 0:
                continue

            # get user object
            item = users[position]
            user = self.bot.get_user(item["user_id"])
            if user is None:
                user = await self.bot.fetch_user(item["user_id"])
            if user is None:
                user_name = "_(Unknown user)_"
            else:
                user_name = discord.utils.escape_mentions(user.display_name)

            # get position string
            # fmt: off
            if item["user_id"] == ctx.author.id:
                lines.append(text.fill("boards", "target template",
                    index=f"{position+1:>2}", name=user_name, count=f"{item['count']:>5}"))
            else:
                lines.append(text.fill("boards", "user template",
                    index=f"{position+1:>2}", name=user_name, count=f"{item['count']:>5}"))
            # fmt: on

        if len(lines) > 0:
            embed.add_field(
                name=text.get("boards", "author position"), value="\n".join(lines), inline=False,
            )

        await ctx.send(embed=embed)

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
        bot_dev = self.bot.get_channel(config.channel_botdev)
        channels = repository.get_user_channels()
        results = None
        tasks = []
        async with bot_dev.typing():

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
                                messages = await self.get_history(channel, None)

                        if len(messages) > 0:
                            tasks.append(self.msg_iter(messages))

        for task in tasks:
            await task

        await bot_dev.send(text.get("boards", "synced"))


def setup(bot):
    bot.add_cog(Boards(bot))

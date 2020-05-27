import asyncio
from datetime import datetime

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

    def sort_channels(self, lis):
        results = []
        for ch in lis:
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

    def sort_userchannel(self, lis):
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

    def sort_users(self, lis):
        results = []
        for ch in lis:
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

    @commands.cooldown(rate=1, per=120.0, type=commands.BucketType.user)
    @commands.command(description=text.get("boards", "channel board"))
    async def channelboard(self, ctx):
        await asyncio.sleep(0.5)
        user_channels = repository.get_user_channels()

        if not user_channels:
            ctx.send(text.get("boards", "not found"))
            return

        results = self.sort_channels(user_channels)

        embed = discord.Embed(title=text.get("boards", "user board title"), color=config.color)
        value = ""
        for idx, row in enumerate(results):
            channel = self.bot.get_channel(row["channel_id"])
            if idx < config.board_top:
                if value == "":
                    value = text.fill(
                        "boards",
                        "channel template",
                        index=idx + 1,
                        guild=channel.guild.name,
                        name=channel.name,
                        count=row["count"],
                    )
                else:
                    value += "\n" + text.fill(
                        "boards",
                        "channel template",
                        index=idx + 1,
                        guild=channel.guild.name,
                        name=channel.name,
                        count=row["count"],
                    )

            if idx > config.board_top:
                break

        embed.add_field(
            name=text.fill("boards", "top number", top=config.board_top), value=value, inline=False
        )
        await ctx.send(embed=embed)

    @commands.cooldown(rate=1, per=120.0, type=commands.BucketType.user)
    @commands.command(description=text.get("boards", "user board"))
    async def userboard(self, ctx):
        await asyncio.sleep(0.5)
        user_channels = repository.get_user_channels()

        if not user_channels:
            ctx.send(text.get("boards", "not found"))
            return

        results = self.sort_users(user_channels)

        embed = discord.Embed(title=text.get("boards", "user board title"), color=config.color)
        value = ""
        author_position = -1
        for idx, row in enumerate(results):
            if ctx.author.id == row["user_id"]:
                author_position = idx
            if idx < config.board_top:
                user = await self.bot.fetch_user(row["user_id"])
                if value == "":
                    if author_position == idx:
                        value = "\n" + text.fill(
                            "boards",
                            "author user",
                            index=idx + 1,
                            name=user.name,
                            count=row["count"],
                        )
                    else:
                        value = text.fill(
                            "boards",
                            "user template",
                            index=idx + 1,
                            name=user.name,
                            count=row["count"],
                        )
                elif author_position == idx:
                    value += "\n" + text.fill(
                        "boards", "author user", index=idx + 1, name=user.name, count=row["count"]
                    )
                else:
                    value += "\n" + text.fill(
                        "boards",
                        "user template",
                        index=idx + 1,
                        name=user.name,
                        count=row["count"],
                    )

            if idx > config.board_top and author_position != -1:
                break

        embed.add_field(
            name=text.fill("boards", "top number", top=config.board_top), value=value, inline=False
        )

        user_pos = [
            author_position - 2,
            author_position - 1,
            author_position,
            author_position + 1,
            author_position + 2,
        ]
        value = ""
        for pos in user_pos:
            if pos >= 0 and pos <= len(results) - 1:
                row = results[pos]
                user = await self.bot.fetch_user(row["user_id"])
                if value == "":
                    if author_position == pos:
                        value = "\n" + text.fill(
                            "boards",
                            "author user",
                            index=author_position + 1,
                            name=user.name,
                            count=row["count"],
                        )
                    else:
                        value = text.fill(
                            "boards",
                            "user template",
                            index=pos + 1,
                            name=user.name,
                            count=row["count"],
                        )
                elif author_position == pos:
                    value += "\n" + text.fill(
                        "boards",
                        "author user",
                        index=author_position + 1,
                        name=user.name,
                        count=row["count"],
                    )
                else:
                    value += "\n" + text.fill(
                        "boards",
                        "user template",
                        index=pos + 1,
                        name=user.name,
                        count=row["count"],
                    )
        embed.add_field(name=text.get("boards", "author position"), value=value, inline=False)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if (
            not isinstance(message.channel, PrivateChannel)
            and not isinstance(message.channel, VoiceChannel)
            and not isinstance(message.channel, CategoryChannel)
        ):
            if (
                message.author.id not in config.board_ignored_users
                and message.channel.id not in config.board_ignored_channels
            ):
                channel_id = message.channel.id
                user_id = message.author.id
                guild_id = message.guild.id
                last_message_at = message.created_at
                last_message_id = message.id
                repository.increment(
                    channel_id=channel_id,
                    user_id=user_id,
                    guild_id=guild_id,
                    last_message_at=last_message_at,
                    last_message_id=last_message_id,
                )
                ch_repo = repository.get_channel(channel_id)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if (
            not isinstance(message.channel, PrivateChannel)
            and not isinstance(message.channel, VoiceChannel)
            and not isinstance(message.channel, CategoryChannel)
        ):
            if (
                message.author.id not in config.board_ignored_users
                and message.channel.id not in config.board_ignored_channels
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
        async with bot_dev.typing():

            if channels is not None:
                results = self.sort_channels(channels)

            for guild in self.bot.guilds:
                for channel in guild.channels:
                    if (
                        not isinstance(channel, PrivateChannel)
                        and not isinstance(channel, VoiceChannel)
                        and not isinstance(channel, CategoryChannel)
                        and channel.id not in config.board_ignored_channels
                    ):
                        if results is None:
                            messages = await channel.history(
                                limit=None, oldest_first=True
                            ).flatten()
                        else:
                            for res in results:
                                if res["channel_id"] == channel.id:
                                    try:
                                        after = await channel.fetch_message(
                                            id=res["last_message_id"]
                                        )
                                    except discord.errors.NotFound:
                                        after = res["last_message_at"]

                                    messages = await channel.history(
                                        limit=None, after=after, oldest_first=True
                                    ).flatten()
                                    break
                            else:
                                messages = await channel.history(
                                    limit=None, oldest_first=True
                                ).flatten()

                        for msg in messages:
                            if msg.author.id not in config.board_ignored_users:
                                channel_id = msg.channel.id
                                user_id = msg.author.id
                                guild_id = msg.guild.id
                                last_message_at = msg.created_at
                                last_message_id = msg.id

                                repository.increment(
                                    channel_id=channel_id,
                                    user_id=user_id,
                                    guild_id=guild_id,
                                    last_message_at=last_message_at,
                                    last_message_id=last_message_id,
                                )
        await bot_dev.send(text.get("boards", "synced"))


def setup(bot):
    bot.add_cog(Boards(bot))

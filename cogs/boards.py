import re
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
    """Voting based commands"""

    def __init__(self, bot):
        self.bot = bot
        self.handled = []

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.check(check.is_mod)
    @commands.command(
        rest_is_raw=True,
        brief=text.get("vote", "vote_desc"),
        description=text.get("vote", "vote_desc"),
        help=text.fill("vote", "vote_help", prefix=config.prefix),
    )
    async def channelboard(self, ctx):
        channels = repository.get_channels()
        results = []
        if channels is not None:
            for ch in channels:
                for row in results:
                    if row["channel_id"] == ch["channel_id"] and row["guild_id"] == ch["guild_id"]:
                        row["count"] += ch["count"]
                        if row["last_message_at"] < ch["last_message_at"]:
                            row["last_message_at"] = ch["last_message_at"]
                        break
                else:
                    results.append(
                        {
                            "channel_id": ch["channel_id"],
                            "guild_id": ch["guild_id"],
                            "count": ch["count"],
                            "last_message_at": ch["last_message_at"],
                        }
                    )
        results = sorted(results, key=lambda i: (i["count"]), reverse=True)
        embed = discord.Embed(title="Channelboard")
        for idx, row in enumerate(results):
            if idx < 9:
                guild = discord.utils.get(self.bot.guilds, id=row["guild_id"])
                channel = discord.utils.get(guild.channels, id=row["channel_id"])
                embed.add_field(
                    name="**{name}** ({count})".format(name=channel.name, count=row["count"]),
                    value="Last message at {}".format(row["last_message_at"]),
                )
        await ctx.send(embed=embed)

    @commands.check(check.is_mod)
    @commands.command(
        rest_is_raw=True,
        brief=text.get("vote", "vote_desc"),
        description=text.get("vote", "vote_desc"),
        help=text.fill("vote", "vote_help", prefix=config.prefix),
    )
    async def board_build(self, ctx):
        for guild in self.bot.guilds:
            for channel in guild.channels:
                if not isinstance(channel, PrivateChannel):
                    if not isinstance(channel, VoiceChannel) and not isinstance(
                        channel, CategoryChannel
                    ):
                        messages = await channel.history(limit=None, oldest_first=True).flatten()
                        print(len(messages))
                        for idx, msg in enumerate(messages, start=1):
                            if (
                                msg.author.id not in config.board_ignored_users
                                and msg.channel.id not in config.board_ignored_users
                            ):
                                channel_id = msg.channel.id
                                user_id = msg.author.id
                                guild_id = msg.guild.id
                                last_message_at = msg.created_at
                                repository.increment(
                                    channel_id, user_id, guild_id, last_message_at
                                )
        await ctx.send("Successfully built UserChannel database.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if not isinstance(message.channel, PrivateChannel):
            if (
                message.author.id not in config.board_ignored_users
                and message.channel.id not in config.board_ignored_users
            ):
                channel_id = message.channel.id
                user_id = message.author.id
                guild_id = message.guild.id
                last_message_at = message.created_at
                repository.increment(channel_id, user_id, guild_id, last_message_at)


def setup(bot):
    bot.add_cog(Boards(bot))

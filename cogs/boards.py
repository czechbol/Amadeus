import asyncio
from datetime import timezone

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
        super().__init__(bot)
        self.handled = []

    async def get_history(self, channel, after):
        if after is None:
            messages = await channel.history(limit=None, oldest_first=True).flatten()
        else:
            messages = await channel.history(limit=None, after=after, oldest_first=True).flatten()
        return messages

    async def msg_iter(self, messages):
        userchannels = []
        for msg in messages:
            for row in userchannels:
                if (
                    row["channel_id"] == msg.channel.id
                    and row["guild_id"] == msg.guild.id
                    and row["user_id"] == msg.author.id
                ):
                    row["count"] += 1
                    if row["last_msg_at"] < msg.created_at:
                        row["last_msg_at"] = msg.created_at
                    break
            else:
                if msg.webhook_id:
                    is_webhook = True
                else:
                    is_webhook = False
                userchannels.append(
                    {
                        "guild_id": msg.guild.id,
                        "channel_id": msg.channel.id,
                        "user_id": msg.author.id,
                        "is_webhook": is_webhook,
                        "last_msg_at": msg.created_at,
                        "count": 1,
                    }
                )

        for usr_ch in userchannels:
            repository.increment(
                guild_id=usr_ch["guild_id"],
                channel_id=usr_ch["channel_id"],
                user_id=usr_ch["user_id"],
                is_webhook=usr_ch["is_webhook"],
                last_msg_at=usr_ch["last_msg_at"],
                count=usr_ch["count"],
            )

        return

    async def sort_channels(self, lis, all_allowed=False):
        results = []
        for usr_ch in lis:
            if all_allowed is True or (
                usr_ch.channel_id not in config.board_ignored_channels
                and usr_ch.user_id not in config.board_ignored_users
                and not usr_ch.is_webhook
            ):

                for row in results:
                    if row["channel_id"] == usr_ch.channel_id and row["guild_id"] == usr_ch.guild_id:
                        row["count"] += usr_ch.count
                        if row["last_msg_at"] < usr_ch.last_msg_at:
                            row["last_msg_at"] = usr_ch.last_msg_at
                        break
                else:
                    results.append(
                        {
                            "channel_id": usr_ch.channel_id,
                            "guild_id": usr_ch.guild_id,
                            "count": usr_ch.count,
                            "last_msg_at": usr_ch.last_msg_at,
                        }
                    )
        results = sorted(results, key=lambda i: (i["count"]), reverse=True)
        return results

    async def sort_userchannel(self, lis, all_allowed=False):
        results = []
        for usr_ch in lis:
            if all_allowed is True or (
                usr_ch.channel_id not in config.board_ignored_channels
                and usr_ch.user_id not in config.board_ignored_users
                and not usr_ch.is_webhook
            ):
                for row in results:
                    if (
                        row["channel_id"] == usr_ch.channel_id
                        and row["guild_id"] == usr_ch.guild_id
                        and row["user_id"] == usr_ch.user_id
                    ):
                        row["count"] += usr_ch.count
                        if row["last_msg_at"] < usr_ch.last_msg_at:
                            row["last_msg_at"] = usr_ch.last_msg_at
                        break
                else:
                    results.append(
                        {
                            "channel_id": usr_ch.channel_id,
                            "guild_id": usr_ch.guild_id,
                            "user_id": usr_ch.user_id,
                            "count": usr_ch.count,
                            "last_msg_at": usr_ch.last_msg_at,
                        }
                    )
        results = sorted(results, key=lambda i: (i["count"]), reverse=True)
        return results

    async def sort_users(self, lis, all_allowed=False):
        results = []
        for usr_ch in lis:
            if all_allowed is True or (
                usr_ch.channel_id not in config.board_ignored_channels
                and usr_ch.user_id not in config.board_ignored_users
                and not usr_ch.is_webhook
            ):
                for row in results:
                    if row["user_id"] == usr_ch.user_id:
                        row["count"] += usr_ch.count
                        if row["last_msg_at"] < usr_ch.last_msg_at:
                            row["last_msg_at"] = usr_ch.last_msg_at
                        break
                else:
                    results.append(
                        {"user_id": usr_ch.user_id, "count": usr_ch.count, "last_msg_at": usr_ch.last_msg_at}
                    )
        results = sorted(results, key=lambda i: (i["count"]), reverse=True)
        return results

    @commands.cooldown(rate=3, per=120.0, type=commands.BucketType.user)
    @commands.command(description=text.get("boards", "channel board"))
    async def channelboard(self, ctx, offset: int = 0):
        await self.deleteCommand(ctx, now=True)
        await asyncio.sleep(0.1)
        user_channels = repository.get_user_channels()

        if not user_channels:
            return ctx.send(text.get("boards", "not found"))

        results = await self.sort_channels(user_channels)

        offset -= 1  # convert to be zero-indexed

        if offset > len(results):
            return await ctx.send(text.get("boards", "offset too big"))

        boards, pagenum = await self.boards_generator(ctx, results, offset, "channel")

        await self.board_pages(ctx, boards, pagenum)

        return

    @commands.cooldown(rate=3, per=120.0, type=commands.BucketType.user)
    @commands.command(description=text.get("boards", "user board"))
    async def userboard(self, ctx, offset: int = 0):
        await self.deleteCommand(ctx, now=True)
        await asyncio.sleep(0.1)
        user_channels = repository.get_user_channels()

        if not user_channels:
            return ctx.send(text.get("boards", "not found"))

        results = await self.sort_users(user_channels)

        offset -= 1  # convert to be zero-indexed

        if offset > len(results):
            return await ctx.send(text.get("boards", "offset too big"))

        boards, pagenum = await self.boards_generator(ctx, results, offset, "user")

        await self.board_pages(ctx, boards, pagenum)

        return

    @commands.cooldown(rate=3, per=120.0, type=commands.BucketType.user)
    @commands.command()
    async def stalk(self, ctx, member: discord.Member):
        await self.deleteCommand(ctx, now=True)
        await asyncio.sleep(0.1)
        user_channels = repository.get_user_channels()

        if not user_channels:
            return await ctx.send(text.get("boards", "not found"))

        results = await self.sort_users(user_channels)
        for idx, result in enumerate(results):
            if member.id == result["user_id"]:
                offset = idx
                break
        else:
            return await ctx.send(text.get("boards", "not found"))

        boards, pagenum = await self.boards_generator(ctx, results, offset, "stalk")

        await self.board_pages(ctx, boards, pagenum)

        return

    @commands.cooldown(rate=3, per=120.0, type=commands.BucketType.user)
    @commands.command()
    async def channelinfo(self, ctx, channel: discord.TextChannel):
        await self.deleteCommand(ctx, now=True)
        await asyncio.sleep(0.1)
        channels = repository.get_user_channels()
        all_results = await self.sort_channels(channels)
        users = await self.sort_users(repository.get_channel(channel.id))
        offset = -1

        if not users:
            return await ctx.send(text.get("boards", "not found"))

        for idx, result in enumerate(all_results, start=1):
            if result["channel_id"] == channel.id:
                total_count = result["count"]
                last_msg_at = result["last_msg_at"]
                position = idx

        for user in users:
            if user["last_msg_at"] == last_msg_at:
                user = self.bot.get_user(user["user_id"])
                if user is None:
                    try:
                        user = await self.bot.fetch_user(user["user_id"])
                        user_name = discord.utils.escape_markdown(f"{user.display_name}#{user.discriminator}")
                    except discord.errors.NotFound:
                        user_name = "_(Unknown user)_"
                else:
                    user_name = discord.utils.escape_markdown(f"{user.display_name}#{user.discriminator}")
                break
        else:
            user_name = "_(Unknown user)_"

        last_msg_at = last_msg_at.replace(tzinfo=timezone.utc).astimezone(tz=None)
        last_msg_at = last_msg_at.strftime("%d.%m.%Y %H:%M:%S")

        embed = self.create_embed(author=ctx.message.author, title=text.get("boards", "channel info title"))
        embed.add_field(name="Jméno", value=str(channel.name), inline=True)
        embed.add_field(name="ID", value=str(channel.id), inline=True)
        embed.add_field(name="Server", value=str(channel.guild.name), inline=True)
        try:
            embed.add_field(name="Kategorie", value=str(channel.category.name), inline=True)
        except AttributeError:
            pass
        embed.add_field(name="Poslední zpráva", value=f"{user_name}\n{last_msg_at}", inline=True)
        embed.add_field(name="Celkový počet zpráv", value=str(total_count), inline=True)
        embed.add_field(
            name="Pozice mezi kanály", value="{0}/{1}".format(position, len(all_results)), inline=True
        )
        embeds = []
        embeds.append(embed)
        boards, pagenum = await self.boards_generator(ctx, users, offset, "channel info")
        embeds += boards

        await self.board_pages(ctx, embeds, pagenum)
        return

    @commands.cooldown(rate=3, per=120.0, type=commands.BucketType.user)
    @commands.command()
    async def userinfo(self, ctx, member: discord.Member):
        await self.deleteCommand(ctx, now=True)
        await asyncio.sleep(0.1)
        users = repository.get_user_channels()
        all_results = await self.sort_users(users)
        channels = await self.sort_channels(repository.get_user(member.id))
        offset = -1

        if not channels:
            return await ctx.send(text.get("boards", "not found"))

        for idx, result in enumerate(all_results, start=1):
            if result["user_id"] == member.id:
                total_count = result["count"]
                last_msg_at = result["last_msg_at"]
                position = idx
        for channel in channels:
            if channel["last_msg_at"] == last_msg_at:
                last_channel = self.bot.get_channel(channel["channel_id"])
                channel_name = last_channel.name
        role_list = []
        for role in member.roles:
            if role.name != "@everyone":
                role_list.append(role.name)

        role_list.reverse()
        last_msg_at = last_msg_at.replace(tzinfo=timezone.utc).astimezone(tz=None)
        last_msg_at = last_msg_at.strftime("%d.%m.%Y %H:%M:%S")
        joined_at = member.joined_at.replace(tzinfo=timezone.utc).astimezone(tz=None)
        joined_at = joined_at.strftime("%d.%m.%Y\n%H:%M:%S")
        joined_dc = member.created_at.replace(tzinfo=timezone.utc).astimezone(tz=None)
        joined_dc = joined_dc.strftime("%d.%m.%Y\n%H:%M:%S")

        if member.colour != discord.Colour.default():
            embed = self.create_embed(
                author=ctx.message.author, title=text.get("boards", "user info title"), colour=member.colour
            )
        else:
            embed = self.create_embed(author=ctx.message.author, title=text.get("boards", "user info title"))

        status = "Do not diturb" if str(member.status) == "dnd" else str(member.status).title()

        embed.set_thumbnail(url=member.avatar_url)
        embed.add_field(
            name="Jméno",
            value=str(f"{member.display_name}\n({member.name}#{member.discriminator})"),
            inline=True,
        )
        embed.add_field(name="ID", value=str(member.id), inline=True)
        embed.add_field(name="Status", value=status, inline=True)
        embed.add_field(name="Účet založen", value=str(joined_dc), inline=True)
        embed.add_field(name="Připojen", value=str(joined_at), inline=True)
        embed.add_field(name="Počet zpráv", value=str(total_count), inline=True)
        embed.add_field(
            name="Pozice mezi uživateli", value="{0}/{1}".format(position, len(all_results)), inline=True
        )
        if check.is_mod(ctx):
            embed.add_field(name="Poslední zpráva", value=f"{channel_name}\n{last_msg_at}", inline=True)
        embed.add_field(name="Role", value=", ".join(str(r) for r in role_list), inline=False)
        if check.is_mod(ctx):
            embeds = []
            embeds.append(embed)
            boards, pagenum = await self.boards_generator(ctx, channels, offset, "user info")
            embeds += boards
            await self.board_pages(ctx, embeds, pagenum)
        else:
            await ctx.send(embed=embed, delete_after=config.delay_embed)

        return

    async def boards_generator(self, ctx, results, offset, typ):
        # splits results into config.board_top sized chunks (chunks = list of lists)
        chunks = [results[i : i + config.board_top] for i in range(0, len(results), config.board_top)]

        boards = []
        author_position = -1
        # Iterates through chunks to get pages
        for idx, chunk in enumerate(chunks):
            chunk_position = idx * config.board_top

            embed = self.create_embed(
                author=ctx.message.author,
                title=text.get("boards", typ + " board title"),
                description=text.get("boards", typ + " board desc"),
            )

            pagenum = 0  # index of board page to show first
            lines = []
            # Iterates through users/channels in chunk to get lines of a single board
            for pos, item in enumerate(chunk):
                position = chunk_position + pos  # item position among all items

                index = f"{position + 1:>2}"
                count = f"{item['count']:>5}"
                if typ == "channel" or typ == "user info":
                    channel = self.bot.get_channel(item["channel_id"])
                    if channel is None:
                        try:
                            channel = await self.bot.fetch_user(item["channel_id"])
                        except discord.errors.NotFound:
                            continue
                    name = "#{}".format(channel.name)
                else:
                    user = self.bot.get_user(item["user_id"])
                    if user is None:
                        try:
                            user = await self.bot.fetch_user(item["user_id"])
                            user_name = discord.utils.escape_markdown(user.display_name)
                        except discord.errors.NotFound:
                            user_name = "_(Unknown user)_"
                    else:
                        user_name = discord.utils.escape_markdown(user.display_name)
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
                            "boards",
                            "template guild",
                            index=index,
                            count=count,
                            name=name,
                            guild=guild,
                        )
                    )
                else:
                    lines.append(
                        text.fill(
                            "boards",
                            "template",
                            index=index,
                            count=count,
                            name=name,
                        )
                    )

            title = "top number" if idx == 0 else "top offset"

            embed.add_field(
                name=text.fill("boards", title, top=config.board_top, offset=(idx * config.board_top) + 1),
                value="\n".join(lines),
                inline=False,
            )

            boards.append(embed)

        for idx, board in enumerate(boards):
            chunk_position = idx * config.board_top
            # adds the YOUR POSITION field for userboard
            if (typ == "user" or typ == "channel info") and (
                not (chunk_position <= author_position <= chunk_position + config.board_top)
                and author_position != -1
            ):
                lines = []
                range_floor = author_position - config.board_around
                range_ceiling = author_position + config.board_around + 1
                for position in range(range_floor, range_ceiling):

                    # do not wrap around (if the 'around' number is too high)
                    if position < 0:
                        continue

                    # get user object
                    item = results[position]
                    user = self.bot.get_user(item["user_id"])
                    if user is None:
                        try:
                            user = await self.bot.fetch_user(item["user_id"])
                            user_name = discord.utils.escape_markdown(user.display_name)
                        except discord.errors.NotFound:
                            user_name = "_(Unknown user)_"
                    else:
                        user_name = discord.utils.escape_markdown(user.display_name)

                    # get position string
                    index = f"{position + 1:>2}"
                    count = f"{item['count']:>5}"
                    name = "{}".format(user_name)
                    if position == author_position:
                        name = "**" + name + "**"

                    lines.append(
                        text.fill(
                            "boards",
                            "template",
                            index=index,
                            name=name,
                            count=count,
                        )
                    )

                if len(lines) > 0:
                    board.add_field(
                        name=text.get("boards", "author position"),
                        value="\n".join(lines),
                        inline=False,
                    )

        return boards, pagenum

    async def board_pages(self, ctx, boards, pagenum=0):
        msg = await ctx.send(embed=boards[pagenum])
        await msg.add_reaction("◀️")
        await msg.add_reaction("▶️")
        while True:

            def chk(reaction, user):
                return (
                    reaction.message.id == msg.id
                    and (str(reaction.emoji) == "◀️" or str(reaction.emoji) == "▶️")
                    and not user == self.bot.user
                )

            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", check=chk, timeout=config.delay_embed
                )
            except asyncio.TimeoutError:
                if msg.channel != self.bot.get_channel(config.channel_mods) or pagenum != 0:
                    try:
                        await msg.delete()
                    except discord.errors.Forbidden:
                        pass
                else:
                    await msg.clear_reaction("◀️")
                    await msg.clear_reaction("▶️")
                break
            else:
                if str(reaction.emoji) == "◀️":
                    pagenum -= 1
                    if pagenum < 0:
                        pagenum = len(boards) - 1
                    try:
                        await msg.remove_reaction("◀️", user)
                    except discord.errors.Forbidden:
                        pass
                    await msg.edit(embed=boards[pagenum])
                if str(reaction.emoji) == "▶️":
                    pagenum += 1
                    if pagenum >= len(boards):
                        pagenum = 0
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
            if message.webhook_id:
                is_webhook = True
            else:
                is_webhook = False
            repository.increment(
                guild_id=message.guild.id,
                channel_id=message.channel.id,
                user_id=message.author.id,
                is_webhook=is_webhook,
                last_msg_at=message.created_at,
                count=1,
            )

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
            last_msg_at = message.created_at
            repository.decrement(
                channel_id=channel_id,
                user_id=user_id,
                guild_id=guild_id,
                last_msg_at=last_msg_at,
            )

    @commands.Cog.listener()
    async def on_ready(self):
        channels = repository.get_user_channels()
        results = None
        admin = self.bot.get_user(config.admin_id)
        messages = []

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
                            if messages is None:
                                msgs = await self.get_history(channel, None)
                        else:
                            for res in results:
                                if res["channel_id"] == channel.id:
                                    after = res["last_msg_at"]
                                    msgs = await self.get_history(channel, after)
                                    break
                            else:
                                try:
                                    msgs = await self.get_history(channel, None)
                                except discord.errors.Forbidden:
                                    await self.log(
                                        level="warning",
                                        message="Forbidden getting history for channel {channel} in guild {guild}".format(
                                            channel=channel, guild=guild.name
                                        ),
                                    )

                        if len(msgs) > 0:
                            messages.extend(msgs)
        await self.msg_iter(messages)

        await admin.send(text.fill("boards", "synced", count=len(messages)))


def setup(bot):
    bot.add_cog(Boards(bot))

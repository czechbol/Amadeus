import asyncio
import datetime
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
                        "guild_name": msg.guild.name,
                        "channel_id": msg.channel.id,
                        "channel_name": msg.channel.name,
                        "user_id": msg.author.id,
                        "user_name": msg.author.display_name,
                        "is_webhook": is_webhook,
                        "last_msg_at": msg.created_at,
                        "count": 1,
                    }
                )

        for usr_ch in userchannels:
            repository.increment(
                guild_id=usr_ch["guild_id"],
                guild_name=usr_ch["guild_name"],
                channel_id=usr_ch["channel_id"],
                channel_name=usr_ch["channel_name"],
                user_id=usr_ch["user_id"],
                user_name=usr_ch["user_name"],
                is_webhook=usr_ch["is_webhook"],
                last_msg_at=usr_ch["last_msg_at"],
                count=usr_ch["count"],
            )

        return

    @commands.command(description=text.get("boards", "channel board"))
    async def channelboard(self, ctx, offset: int = 0):
        await asyncio.sleep(0.1)
        if not isinstance(ctx.channel, PrivateChannel):
            channel_counts = repository.get_channel_counts(guild_id=ctx.guild.id)
        else:
            channel_counts = repository.get_channel_counts()  # TODO Do we want i to work in DMs?

        if not channel_counts:
            return ctx.send(text.get("boards", "not found"))

        if offset > len(channel_counts):
            return await ctx.send(text.get("boards", "offset too big"))

        boards, pagenum = await self.boards_generator(
            ctx=ctx, counts=channel_counts, offset=offset, typ="channel"
        )

        await self.board_pages(ctx, boards, pagenum)

        return

    @commands.command(description=text.get("boards", "user board"))
    async def userboard(self, ctx, offset: int = 0):
        await asyncio.sleep(0.1)

        if not isinstance(ctx.channel, PrivateChannel):
            user_counts = repository.get_user_counts(guild_id=ctx.guild.id)
        else:
            user_counts = repository.get_user_counts()  # TODO Do we want i to work in DMs?

        if not user_counts:
            return ctx.send(text.get("boards", "not found"))

        if offset > len(user_counts):
            return await ctx.send(text.get("boards", "offset too big"))

        boards, pagenum = await self.boards_generator(ctx=ctx, counts=user_counts, offset=offset, typ="user")

        await self.board_pages(ctx, boards, pagenum)

        return

    @commands.command()
    async def stalk(self, ctx, member: discord.Member):
        await asyncio.sleep(0.1)
        if not isinstance(ctx.channel, PrivateChannel):
            user_counts = repository.get_user_counts(guild_id=ctx.guild.id)
            ranked_user = repository.get_user_ranked(guild_id=ctx.guild.id, user_id=member.id)
        else:
            user_counts = repository.get_user_counts()  # TODO Do we want i to work in DMs?
            ranked_user = repository.get_user_ranked(user_id=member.id)

        if user_counts == [] or ranked_user is None:
            return ctx.send(text.get("boards", "not found"))

        boards, pagenum = await self.boards_generator(
            ctx=ctx, counts=user_counts, offset=ranked_user.rank, typ="stalk"
        )

        await self.board_pages(ctx, boards, pagenum)

        return

    @commands.command()
    async def channelinfo(self, ctx, channel: discord.TextChannel):
        await asyncio.sleep(0.1)
        if not isinstance(ctx.channel, PrivateChannel):
            user_counts = repository.get_user_counts(guild_id=ctx.guild.id, channel_id=channel.id)
            ranked_channel = repository.get_channel_ranked(guild_id=ctx.guild.id, channel_id=channel.id)
            channel_sum = repository.get_channel_sum(guild_id=ctx.guild.id)
            result = repository.get_last(guild_id=ctx.guild.id, channel_id=channel.id)
        else:  # TODO Do we want i to work in DMs?
            user_counts = repository.get_user_counts(channel_id=channel.id)
            ranked_channel = repository.get_channel_ranked(channel_id=channel.id)
            channel_sum = repository.get_channel_sum()
            result = repository.get_last(channel_id=channel.id)

        if user_counts is None:
            return await ctx.send(text.get("boards", "not found"))

        if result is not None:
            user = self.bot.get_user(result.user_id)
            if user is None:
                try:
                    user = await self.bot.fetch_user(result.user_id)
                    user_name = discord.utils.escape_markdown(f"{user.display_name}#{user.discriminator}")
                except discord.errors.NotFound:
                    user_name = "_(Unknown user)_"
            else:
                user_name = discord.utils.escape_markdown(f"{user.display_name}#{user.discriminator}")
        else:
            user_name = "_(Unknown user)_"

        last_msg_at = result.last_msg_at.replace(tzinfo=timezone.utc).astimezone(tz=None)
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
        embed.add_field(name="Celkový počet zpráv", value=str(ranked_channel.total), inline=True)
        embed.add_field(name="Pozice mezi kanály", value=f"{ranked_channel.rank}/{channel_sum}", inline=True)
        embeds = []
        embeds.append(embed)
        boards, pagenum = await self.boards_generator(ctx=ctx, counts=user_counts, typ="channel info")
        embeds += boards

        await self.board_pages(ctx, embeds, pagenum)
        return

    @commands.command()
    async def userinfo(self, ctx, member: discord.Member):
        await asyncio.sleep(0.1)
        if not isinstance(ctx.channel, PrivateChannel):
            channel_counts = repository.get_channel_counts(guild_id=ctx.guild.id, user_id=member.id)
            ranked_user = repository.get_user_ranked(guild_id=ctx.guild.id, user_id=member.id)
            user_sum = repository.get_user_sum(guild_id=ctx.guild.id)
            result = repository.get_last(guild_id=ctx.guild.id, user_id=member.id)
        else:  # TODO Do we want i to work in DMs?
            channel_counts = repository.get_channel_counts(user_id=member.id)
            ranked_user = repository.get_user_ranked(user_id=member.id)
            user_sum = repository.get_user_sum()
            result = repository.get_last(user_id=member.id)

        if not channel_counts:
            return await ctx.send(text.get("boards", "not found"))

        last_channel = self.bot.get_channel(result.channel_id)
        channel_name = last_channel.name
        role_list = []
        for role in member.roles:
            if role.name != "@everyone":
                role_list.append(role.name)
        role_list.reverse()

        last_msg_at = result.last_msg_at.replace(tzinfo=timezone.utc).astimezone(tz=None)
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
        embed.add_field(name="Počet zpráv", value=str(ranked_user.total), inline=True)
        embed.add_field(name="Pozice mezi uživateli", value=f"{ranked_user.rank}/{user_sum}", inline=True)
        embed.add_field(name="Poslední zpráva", value=f"{channel_name}\n{last_msg_at}", inline=True)
        embed.add_field(name="Role", value=", ".join(str(r) for r in role_list), inline=False)

        embeds = []
        embeds.append(embed)
        boards, pagenum = await self.boards_generator(ctx=ctx, counts=channel_counts, typ="user info")
        embeds += boards
        await self.board_pages(ctx, embeds, pagenum)

        return

    async def boards_generator(self, ctx=None, counts=None, offset=0, typ=None):
        if ctx is None:
            return None
        elif counts is None:
            return None
        elif typ is None:
            return None
        # splits results into config.board_top sized chunks (chunks = list of lists)
        chunks = [counts[i : i + config.board_top] for i in range(0, len(counts), config.board_top)]

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
            for item in chunk:
                rank = f"{item.rank:>2}"
                count = f"{item.total:>5}"
                if typ == "channel" or typ == "user info":
                    name = "#{}".format(item.channel_name)
                else:
                    name = discord.utils.escape_markdown(item.user_name)

                    if item.user_id == ctx.author.id:  # displays author in bold, saves author position
                        author_position = item.rank - 1
                        name = "**" + name + "**"

                if item.rank == offset:  # displays offset user/channel in bold, saves page number
                    pagenum = idx
                    name = "**" + name + "**"
                if typ == "channel" and (
                    isinstance(ctx.channel, PrivateChannel) or item.guild_id != ctx.guild.id
                ):
                    # only shows channel guild if message didn't come from guild or message guild is different than board channel's guild
                    guild = discord.utils.escape_markdown(item.guild_name)
                    lines.append(
                        text.fill(
                            "boards",
                            "template guild",
                            index=rank,
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
                            index=rank,
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
                    item = counts[position]
                    name = discord.utils.escape_markdown(item.user_name)

                    # get position string
                    rank = f"{item.rank:>2}"
                    count = f"{item.total:>5}"
                    if position == author_position:
                        name = "**" + name + "**"

                    lines.append(
                        text.fill(
                            "boards",
                            "template",
                            index=rank,
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
                guild_name=message.guild.name,
                channel_id=message.channel.id,
                channel_name=message.channel.name,
                user_id=message.author.id,
                user_name=message.author.display_name,
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
            repository.decrement(
                guild_id=message.guild.id,
                guild_name=message.guild.name,
                channel_id=message.channel.id,
                channel_name=message.channel.name,
                user_id=message.author.id,
                user_name=message.author.display_name,
                last_msg_at=message.created_at,
            )

    @commands.Cog.listener()
    async def on_ready(self):
        channel_counts = repository.get_channel_counts(webhooks=True, include_filtered=True)
        admin = self.bot.get_user(config.admin_id)
        messages = []

        async with admin.typing():
            for guild in self.bot.guilds:
                for channel in guild.channels:
                    if (
                        not isinstance(channel, PrivateChannel)
                        and not isinstance(channel, VoiceChannel)
                        and not isinstance(channel, CategoryChannel)
                    ):

                        if channel_counts is None:
                            msgs = await self.get_history(channel, None)
                        else:
                            count = next((x for x in channel_counts if channel.id == x.channel_id), False)
                            if count:
                                after = count.last_msg_at
                                msgs = await self.get_history(channel, after)
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

    @commands.check(check.is_bot_owner)
    @commands.command()
    async def boards_regenerate_names(self, ctx):
        a = datetime.datetime.now()

        for guild in self.bot.guilds:
            channels = repository.get_channel_counts(guild_id=guild.id, webhooks=True, include_filtered=True)
            repository.update_guild(guild_id=guild.id, guild_name=guild.name)

            for chnl in channels:
                channel = guild.get_channel(chnl.channel_id)
                if channel is None:
                    try:
                        channel = await self.bot.fetch_channel(chnl.channel_id)
                    except discord.errors.NotFound:
                        await self.log(
                            level="warning",
                            message=f"Couldn't find channel for - guild_id:{chnl.guild_id} guild_name:{chnl.guild_name} channel_id:{chnl.channel_id}",
                        )
                        repository.delete_channel(channel_id=chnl.channel_id)
                        continue
                    except discord.errors.Forbidden:
                        await self.log(
                            level="warning",
                            message=f"Couldn't find channel name for - guild_id:{chnl.guild_id} guild_name:{chnl.guild_name} channel_id:{chnl.channel_id}",
                        )
                        continue
                repository.update_channel(channel_id=chnl.channel_id, channel_name=channel.name)

        b = datetime.datetime.now()
        c = b - a
        await ctx.send(f"Regenerated channels in {c}")
        users = repository.get_user_counts(webhooks=True, include_filtered=True)
        for usr in users:
            user = self.bot.get_user(usr.user_id)
            if user is None:
                try:
                    user = await self.bot.fetch_user(usr.user_id)
                    user_name = user.display_name
                except discord.errors.NotFound:
                    await self.log(
                        level="warning", message=f"Couldn't find username for user_id:{usr.user_id}"
                    )
                    user_name = "_(Unknown user)_"
            else:
                user_name = user.display_name
            repository.update_user(user_id=usr.user_id, user_name=user_name)

        e = datetime.datetime.now()
        c = e - a
        await ctx.send(f"Database updated in {c}")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.display_name != after.display_name:
            repository.update_user(user_id=after.id, user_name=after.display_name)
        return

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if before.name != after.name:
            repository.update_channel(channel_id=after.id, channel_name=after.name)
        return

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        if before.name != after.name:
            repository.update_guild(guild_id=after.id, guild_name=after.name)
        return


def setup(bot):
    bot.add_cog(Boards(bot))

import re
import asyncio
from datetime import datetime
from datetime import timedelta

import dateutil
import dateutil.parser as dparser

import discord
from discord.ext import commands
from discord.utils import escape_markdown, escape_mentions

from core import basecog
from core.text import text
from core.config import config
from repository import vote_repo


repository = vote_repo.VoteRepository()


class Vote(basecog.Basecog):
    """Voting based commands"""

    def __init__(self, bot):
        super().__init__(bot)
        self.handled = []

    async def fetch_repo_votes(self):
        lis = repository.get_list()
        if lis is not None:
            votes = []
            for v in lis:
                try:
                    channel = self.bot.get_channel(v["channel_id"])
                    vote_msg = await channel.fetch_message(v["message_id"])
                    edit_msg = await channel.fetch_message(v["edit_id"])
                    date = v["date"]
                    asyncio.create_task(self.loop(vote_msg, edit_msg, date))
                    votes.append(v["message_id"])
                except discord.errors.NotFound:
                    repository.del_vote(
                        channel_id=v["channel_id"], message_id=v["message_id"]
                    )

    async def find_emotes(self, vote_msg):
        lines = vote_msg.content.split("\n")
        votes = []
        for line in lines:
            emote = re.match(r"<:\w*:\d*>", line)
            if emote is not None:
                for emoji in self.bot.emojis:
                    if str(emoji) in line:
                        votes.append(
                            {
                                "emote": emoji,
                                "option": line.replace(str(emoji) + " ", ""),
                                "num_votes": 0,
                            }
                        )
                        break
        return votes

    async def check_reactions(self, raw_reaction, vote_msg, votes, edit_msg, date):
        try:
            if raw_reaction.message_id == vote_msg.id:
                if vote_msg in self.bot.cached_messages:
                    content = text.get("vote", "vote_count")
                    for reaction in vote_msg.reactions:
                        for option in votes:
                            if reaction.emoji == option["emote"]:
                                option["num_votes"] = reaction.count
                    votes = sorted(votes, key=lambda i: (i["num_votes"]), reverse=True)
                    for option in votes:
                        content += text.fill(
                            "vote",
                            "option",
                            option=option["option"],
                            num=option["num_votes"] - 1,
                        )
                    content += text.fill(
                        "vote", "ends", date=date.strftime("%Y-%m-%d %H:%M:%S")
                    )
                    content = escape_mentions(escape_markdown(content))
                    await edit_msg.edit(content=content)
                else:
                    if text.get("vote", "not_in_cache") not in edit_msg.content:
                        edit_msg = await vote_msg.channel.fetch_message(edit_msg.id)
                        if text.get("vote", "not_in_cache") not in edit_msg.content:
                            content = (
                                edit_msg.content
                                + "\n"
                                + text.get("vote", "not_in_cache")
                            )
                            await edit_msg.edit(content=content)
        except UnboundLocalError:
            pass

    async def loop(self, vote_msg, edit_msg, date):
        votes = await self.find_emotes(vote_msg)

        while True:
            if date < datetime.now():
                break
            timeout = (date - datetime.now()).seconds
            pending_tasks = [
                self.bot.wait_for("raw_reaction_add"),
                self.bot.wait_for("raw_reaction_remove"),
            ]

            done_tasks, pending_tasks = await asyncio.wait(
                pending_tasks, return_when=asyncio.FIRST_COMPLETED, timeout=timeout
            )
            for task in done_tasks:
                raw_reaction = await task

            await self.check_reactions(raw_reaction, vote_msg, votes, edit_msg, date)

        if vote_msg not in self.bot.cached_messages:
            vote_msg = await vote_msg.channel.fetch_message(vote_msg.id)

        for reaction in vote_msg.reactions:
            for option in votes:
                if reaction.emoji == option["emote"]:
                    option["num_votes"] = reaction.count

        lines = vote_msg.content.split("\n")

        content = text.fill(
            "vote", "ended", now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        content += lines[0] + "\n"
        votes = sorted(votes, key=lambda i: (i["num_votes"]), reverse=True)
        for option in votes:
            content += text.fill(
                "vote",
                "option",
                option=option["option"],
                num=option["num_votes"] - 1,
            )
        content = escape_mentions(escape_markdown(content))

        await edit_msg.channel.send(content=content)
        repository.del_vote(channel_id=vote_msg.channel.id, message_id=vote_msg.id)
        return

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command(
        rest_is_raw=True,
        brief=text.get("vote", "vote_desc"),
        description=text.get("vote", "vote_desc"),
        help=text.fill("vote", "vote_help", prefix=config.prefix),
    )
    async def vote(self, ctx):
        message = ctx.message
        lines = message.content.split("\n")
        if len(lines) < 3:
            await ctx.send(
                ">>> " + text.fill("vote", "vote_help", prefix=config.prefix)
            )
            return
        now = datetime.now()
        try:
            timex = re.compile(r"[ ](\d*[h])*[ ]*(\d*[m])*[ ]*(\d*[s])*[ ]")
            if timex.search(str(lines[0])) is not None:
                now = datetime.now()
                t = dparser.parse(lines[0], dayfirst=True, fuzzy=True)
                diff = t - now.replace(hour=0, minute=0, second=0)
                date = now + diff
            else:
                date = dparser.parse(lines[0], dayfirst=True, fuzzy=True)
            if now > date:
                date += timedelta(days=1)
        except dateutil.parser._parser.ParserError:
            date = now + timedelta(hours=1)
        votes = []
        for idx, line in enumerate(lines):
            if idx > 0:
                emote = re.match(r"<:\w*:\d*>", line)
                if emote is not None:
                    for emoji in self.bot.emojis:
                        if str(emoji) in line:
                            votes.append(
                                {
                                    "emote": emoji,
                                    "option": line.replace(str(emoji) + " ", ""),
                                    "num_votes": 0,
                                }
                            )
                            break
                    else:
                        await ctx.send(text.get("vote", "emote_unknown"))
                        return
                else:
                    await ctx.send(text.get("vote", "emote_unknown"))
                    return

        for option in votes:
            await ctx.message.add_reaction(option["emote"])

        edit_msg = await ctx.send(
            text.fill("vote", "waiting", date=date.strftime("%Y-%m-%d %H:%M:%S"))
        )
        repository.add_vote(
            channel_id=message.channel.id,
            message_id=message.id,
            edit_id=edit_msg.id,
            date=date.strftime("%Y-%m-%d %H:%M:%S"),
        )

        await self.loop(ctx.message, edit_msg, date)
        return

    @commands.Cog.listener()
    async def on_ready(self):
        await self.fetch_repo_votes()

    @commands.Cog.listener()
    async def on_resumed(self):
        await self.fetch_repo_votes()


def setup(bot):
    bot.add_cog(Vote(bot))

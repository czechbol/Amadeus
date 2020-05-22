import typing
from datetime import datetime
from datetime import timedelta
import dateutil.parser as dparser
import dateutil
import re
import asyncio

from core.config import config

import discord
from discord import Reaction, RawReactionActionEvent, NotFound, HTTPException
from discord.ext import commands
from discord.ext.commands import BadArgument


class Vote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.handled = []


    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command(rest_is_raw=True)
    async def vote(self, ctx):
        """Voting cog"""
        message = ctx.message
        lines = message.content.split("\n")
        if len(lines) < 3:
            await ctx.send("Použití vote:\n`" + config.prefix + "vote [datum] [čas] [otázka]\n[emoji]" \
                     " [odpověď 1]\n[emoji] [odpověď 2]\na tak dále`\n" \
                     "Datum je ve formátu `dd.MM.(yy)`. Čas je ve formátu `hh:mm`. " \
                     "Pouze vyplněný čas použije den odeslání zprávy, " \
                     "pouze vyplněné datum použije čas 00:00. " \
                     "Datum a čas jsou nepovinné argumenty, " \
                     "hlasování bude bez jejich uvedení ukončeno po 1 hodině. " \
                     "Bot pošle po uplynutí zprávu o výsledku," \
                     "když ho mezitím nikdo nevypne. " \
                     "Indikace výherné možnosti přežije i vypnutí.\n"\
                     "Lze použít jen custom emotes ze serverů kde je i bot.")
            return
        now = datetime.now()
        try:
            date = dparser.parse(lines[0], dayfirst=True, fuzzy=True)
            if now > date:
                date += timedelta(days=1)
        except dateutil.parser._parser.ParserError:
            date = now + timedelta(hours=1)
        votes = []
        for line in lines:
            emote = re.match(r'<:\w*:\d*>', line)
            if emote is not None:
                for emoji in self.bot.emojis:
                    if str(emoji) in line:
                        votes.append({"emote":emoji, "option":line.replace(str(emoji)+" ", ""), "num_votes":0})
                        break
                else:
                   await ctx.send("Pro `vote` jde použít jen emotes ze serveru kde jsem.")
                   return
        print(date)
        for option in votes:
            await ctx.message.add_reaction(option["emote"])
        
        msg = await ctx.send("Čekám na hlasy.")

        while True:
            if date < datetime.now():
                break
            timeout = (date - datetime.now()).seconds
            pending_tasks = [self.bot.wait_for('reaction_add'),
                 self.bot.wait_for('reaction_remove')]
            
            done_tasks, pending_tasks = await asyncio.wait(pending_tasks, return_when=asyncio.FIRST_COMPLETED, timeout=timeout)
            for task in done_tasks: 
                reaction, user = await task
            content = "Pořadí hlasů je:\n"

            for reaction in ctx.message.reactions:
                for option in votes:
                    if reaction.emoji == option["emote"]:
                        option["num_votes"] = reaction.count

            votes = sorted(votes, key = lambda i: (i['num_votes']), reverse=True)
            for option in votes:
                content += "{option} - počet hlasů: {num}\n".format(option=option['option'], num=option['num_votes']-1)
            await msg.edit(content=content)
        
        for reaction in ctx.message.reactions:
                for option in votes:
                    if reaction.emoji == option["emote"]:
                        option["num_votes"] = reaction.count

        content = "Hlasování skončilo:\n"
        votes = sorted(votes, key = lambda i: (i['num_votes']), reverse=True)
        for option in votes:
            content += "{option} - počet hlasů: {num}\n".format(option=option['option'], num=option['num_votes']-1)

        await msg.edit(content=content)
        return
        

def setup(bot):
    bot.add_cog(Vote(bot))
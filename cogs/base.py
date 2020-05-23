import datetime

import discord
from discord.ext import commands

from core import basecog
from core.text import text
from core.config import config

boottime = datetime.datetime.now().replace(microsecond=0)

class Base (basecog.Basecog):
    """Basic bot commands"""
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)

    @commands.cooldown (rate=2, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def uptime(self, ctx):
        """Checks bot uptime"""
        now = datetime.datetime.now().replace(microsecond=0)
        delta = now - boottime

        embed = self._getEmbed(ctx)
        embed.add_field(name="Boot", value=str(boottime), inline=False)
        embed.add_field(name="Uptime", value=str(delta), inline=False)
        await ctx.send(embed=embed, delete_after=config.delay_embed)
        await self.deleteCommand(ctx, now=True)

    @commands.command()
    async def ping(self, ctx):
        """Checks bot latency"""
        await ctx.send("pong: **{:.2f} s**".format(self.bot.latency))

    @commands.command(hidden=True)
    async def pong(self, ctx):
        """Really?"""
        await ctx.send(text.get("base", "really"))

def setup(bot):
    bot.add_cog(Base(bot))

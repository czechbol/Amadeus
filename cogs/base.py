import datetime

import discord
from discord.ext import commands

from core import basecog
from core.text import text
from core.config import config

boottime = datetime.datetime.now().replace(microsecond=0)


class Base(basecog.Basecog):
    """Basic bot commands"""

    def __init__(self, bot: commands.Bot):
        super().__init__(bot)

    @commands.cooldown(rate=2, per=20.0, type=commands.BucketType.user)
    @commands.command(description=text.get("base", "uptime_desc"))
    async def uptime(self, ctx):
        now = datetime.datetime.now().replace(microsecond=0)
        delta = now - boottime

        embed = self._getEmbed(ctx)
        embed.add_field(name="Boot", value=str(boottime), inline=False)
        embed.add_field(name="Uptime", value=str(delta), inline=False)
        await ctx.send(embed=embed, delete_after=config.delay_embed)
        await self.deleteCommand(ctx, now=True)

    @commands.command(description=text.get("base", "ping_desc"))
    async def ping(self, ctx):
        await ctx.send("pong: **{:.2f} s**".format(self.bot.latency))

    @commands.command(hidden=True, description=text.get("base", "pong_desc"))
    async def pong(self, ctx):
        await ctx.send(text.get("base", "really"))


def setup(bot):
    bot.add_cog(Base(bot))

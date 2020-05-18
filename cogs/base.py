import datetime

import discord
from discord.ext import commands

from core import basecog
from core.config import config

boottime = datetime.datetime.now().replace(microsecond=0)

class Base (basecog.Basecog):
    """About"""
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)

    @commands.cooldown (rate=2, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def uptime(self, ctx):
        """Bot uptime"""
        now = datetime.datetime.now().replace(microsecond=0)
        delta = now - boottime

        embed = self._getEmbed(ctx)
        embed.add_field(name="Boot", value=str(boottime), inline=False)
        embed.add_field(name="Uptime", value=str(delta), inline=False)
        await ctx.send(embed=embed, delete_after=config.delay_embed)
        await self.deleteCommand(ctx, now=True)

    @commands.command()
    async def ping(self, ctx):
        """Bot latency"""
        await ctx.send("pong: **{:.2f} s**".format(self.bot.latency))

    @commands.cooldown (rate=2, per=60.0, type=commands.BucketType.user)
    @commands.command(aliases=["goddess"])
    async def amadeus(self, ctx):
        """Display information about bot functions"""
        embed = self.reaction.make_embed(1)
        msg = await ctx.send(embed=embed, delete_after=config.delay_embed)
        await self.deleteCommand(ctx)
        await msg.add_reaction("◀")
        await msg.add_reaction("▶")

def setup(bot):
    bot.add_cog(Base(bot))

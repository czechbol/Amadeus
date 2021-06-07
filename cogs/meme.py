from random import choice

import discord
from discord.ext import commands

from core import basecog
from core.text import text


uhoh_ctr = 0


class Meme(basecog.Basecog):
    """Meme bot commands."""

    def __init__(self, bot: commands.Bot):
        super().__init__(bot)

    @commands.command(description=text.get("base", "uhoh_desc"))
    async def uhoh(self, ctx):
        global uhoh_ctr

        await ctx.send(text.fill("base", "uh oh", cnt=uhoh_ctr))

    @commands.command(hidden=True, description=text.get("base", "pong_desc"))
    async def pong(self, ctx):
        await ctx.send(text.get("base", "really"))

    @commands.command(hidden=True)
    async def voice_count(self, ctx):
        channels = ctx.guild.voice_channels
        count = 0
        for channel in channels:
            count += int(len(channel.members))
        await ctx.send(str(count))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        global uhoh_ctr

        if message.content == "PR":
            await message.channel.send("<https://github.com/Czechbol/Amadeus/pulls>")
        elif message.content == "🔧":
            await message.channel.send("<https://github.com/Czechbol/Amadeus/issues>")
        elif "uh oh" in message.content.lower() and not message.author.bot:
            await message.channel.send("uh oh")
            uhoh_ctr += 1

    @commands.command(hidden=True)
    async def oznuk(self, ctx):
        await ctx.send("https://www.vutbr.cz/studis/student.phtml?sn=vystupni_list")

    @commands.cooldown(rate=5, per=120, type=commands.BucketType.user)
    @commands.command(aliases=["rcase", "randomise"])
    async def randomcase(self, ctx, *, message: str = None):
        author_name = ctx.author.display_name
        if message is None:
            text = "O.o"
        else:
            text = "".join(choice((str.upper, str.lower))(c) for c in message[:2000])  # nosec B311
            text = discord.utils.escape_markdown(text)
            text = text.replace("@", "@\u200b")
        text = f"**{author_name}**\n>>> {text}"[:2000]

        await ctx.send(text)


def setup(bot):
    bot.add_cog(Meme(bot))

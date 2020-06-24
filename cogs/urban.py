import re
import discord
import requests
from urllib import parse as url_parse
from discord.ext import commands

from core import basecog
from core.text import text
from core.config import config
from repository import vote_repo


repository = vote_repo.VoteRepository()


class Urban(basecog.Basecog):
    """Weeb shit based commands"""

    def __init__(self, bot):
        self.bot = bot

    def urban_embed(self, dic, pagenum):
        num = pagenum - 1
        lis = dic["list"]
        definition = re.sub(r"[!\[]|[!\]]", "", lis[num]["definition"])
        example = re.sub(r"[!\[]|[!\]]", "", lis[num]["example"])

        embed = discord.Embed(title=lis[num]["word"], url=lis[num]["permalink"])

        embed.add_field(name="Definition", value=definition, inline=False)
        embed.add_field(name="Example", value=example, inline=False)
        """embed.add_field(
            name="Page", value="{curr}/{total}".format(curr=pagenum, total=len(lis)), inline=False,
        )"""  # TODO add pagination support
        return embed

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command(
        brief=text.get("weeb", "sauce_desc"),
        description=text.get("weeb", "sauce_desc"),
        help=text.fill("weeb", "sauce_help", prefix=config.prefix),
    )
    async def urban(self, ctx):
        message = ctx.message
        args = message.content.split(" ")
        args.pop(0)
        if len(args) == 1:
            await ctx.send(">>> " + text.fill("weeb", "sauce_help", prefix=config.prefix))
            return
        search = " ".join(args)
        term = url_parse.quote(search)
        async with ctx.typing():
            try:
                response = requests.get(
                    "http://api.urbandictionary.com/v0/define?term={term}".format(term=term)
                )
                dic = response.json()
                response.raise_for_status()

            except requests.HTTPError as http_err:
                await ctx.send(f"HTTP error occurred: {http_err}")
            except Exception as err:
                await ctx.send(f"Error occurred: {err}")
            else:
                # Request was successful
                embed = self.urban_embed(dic, 1)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Urban(bot))

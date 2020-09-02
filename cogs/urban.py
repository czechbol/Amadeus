import re
import discord
import requests
import asyncio
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

    def urban_embeds(self, ctx, dic):
        lis = dic["list"]
        embed_list = []

        for idx in range(len(lis)):
            definition = re.sub(r"[!\[]|[!\]]", "", lis[idx]["definition"])
            example = re.sub(r"[!\[]|[!\]]", "", lis[idx]["example"])

            if len(definition) > 1024:
                definition = definition[0:1021] + "`…`"
            if len(example) > 1024:
                definition = definition[0:1021] + "`…`"

            embed = self.create_embed(
                author=ctx.message.author,
                title=lis[idx]["word"],
                url=lis[idx]["permalink"],
            )
            embed.add_field(name="Definition", value=definition, inline=False)
            embed.add_field(name="Example", value=example, inline=False)
            embed.add_field(
                name="Page",
                value="{curr}/{total}".format(curr=idx + 1, total=len(lis)),
                inline=False,
            )
            embed_list.append(embed)
        return embed_list

    async def urban_pages(self, ctx, embeds):
        message = await ctx.send(embed=embeds[0])
        pagenum = 0
        await message.add_reaction("◀️")
        await message.add_reaction("▶️")
        while True:

            def check(reaction, user):
                return (
                    reaction.message.id == message.id
                    and (str(reaction.emoji) == "◀️" or str(reaction.emoji) == "▶️")
                    and not user == self.bot.user
                )

            try:
                reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=300.0)
            except asyncio.TimeoutError:
                break
            else:
                if str(reaction.emoji) == "◀️":
                    pagenum -= 1
                    if pagenum < 0:
                        pagenum = len(embeds) - 1
                    try:
                        await message.remove_reaction("◀️", user)
                    except discord.errors.Forbidden:
                        pass
                    await message.edit(embed=embeds[pagenum])
                if str(reaction.emoji) == "▶️":
                    pagenum += 1
                    if pagenum >= len(embeds):
                        pagenum = 0
                    try:
                        await message.remove_reaction("▶️", user)
                    except discord.errors.Forbidden:
                        pass
                    await message.edit(embed=embeds[pagenum])

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command(
        brief=text.get("urban", "urban_desc"),
        description=text.get("urban", "urban_desc"),
        help=text.fill("urban", "urban_help", prefix=config.prefix),
    )
    async def urban(self, ctx):
        await self.deleteCommand(ctx, now=True)
        message = ctx.message
        args = message.content.split(" ")
        if len(args) == 1:
            await ctx.send(">>> " + text.fill("urban", "urban_help", prefix=config.prefix))
            return
        args.pop(0)
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
                embeds = self.urban_embeds(ctx, dic)

        await self.urban_pages(ctx, embeds)

        return


def setup(bot):
    bot.add_cog(Urban(bot))

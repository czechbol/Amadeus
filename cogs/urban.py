import re
import aiohttp
import asyncio
import discord
import dateutil.parser as dparser
from datetime import datetime
from urllib import parse as url_parse
from discord.ext import commands

from core import basecog
from core.text import text
from core.config import config


class UrbanItem:
    __slots__ = ["word", "definition", "example", "permalink", "author", "written_on"]

    def __init__(
        self,
        word: str = None,
        definition: str = None,
        example: str = None,
        permalink: str = None,
        author: str = None,
        written_on: datetime = None,
    ):
        self.word = word
        self.definition = definition
        self.example = example
        self.permalink = permalink
        self.author = author
        self.written_on = written_on

    def __repr__(self):
        return (
            f'<UrbanItem word="{self.word}" definition="{self.definition}" '
            f'example="{self.example}" permalink="{self.permalink}" '
            f'author="{self.author}" written_on="{self.written_on}">'
        )


class Urban(basecog.Basecog):
    """Urbandictionary search"""

    def __init__(self, bot):
        super().__init__(bot)

    def urban_embeds(self, ctx, urban_list):
        embed_list = []

        for idx, item in enumerate(urban_list):
            if len(item.definition) > 1024:
                item.definition = item.definition[0:1021] + "`…`"
            if len(item.example) > 1024:
                item.example = item.example[0:1021] + "`…`"

            embed = self.create_embed(
                author=ctx.message.author, title=item.word, url=item.permalink, timestamp=item.written_on
            )
            if item.definition != "":
                embed.add_field(name="Definition", value=item.definition, inline=False)
            if item.example != "":
                embed.add_field(name="Example", value=item.example, inline=False)

            embed.add_field(
                name="Page",
                value="{curr}/{total}".format(curr=idx + 1, total=len(urban_list)),
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
                    and user == ctx.message.author
                )

            try:
                reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=300.0)
            except asyncio.TimeoutError:
                await message.clear_reactions()
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
                async with aiohttp.ClientSession(raise_for_status=True) as session:
                    async with session.get(
                        f"http://api.urbandictionary.com/v0/define?term={term}"
                    ) as response:
                        json_response = await response.json()
                        lis = json_response["list"]

            except aiohttp.ClientResponseError as e:
                embed = self.create_embed(
                    author=ctx.message.author, title="Critical error:", color=config.color_error
                )
                embed.add_field(
                    name="API replied with:",
                    value=f"`{e.status} {e.message}`"
                    "\n*This could mean UrbanDictionary is experiencing an outage, a network connection error has occured, or you provided a wrong request.*",
                    inline=False,
                )

                await ctx.send(embed=embed)
                return
            else:
                # Request was successful
                urban_list = []
                for item in lis:
                    regex = re.compile(
                        r"^(?:http|ftp)s?://"  # http:// or https://
                        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
                        r"localhost|"  # localhost...
                        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
                        r"(?::\d+)?"  # optional port
                        r"(?:/?|[/?]\S+)$",
                        re.IGNORECASE,
                    )  # Checks for valid URL This exact regex is used by Django (https://github.com/django/django/blob/stable/1.3.x/django/core/validators.py#L45)
                    match_result = re.match(regex, item["permalink"])
                    permalink = match_result.group(0) if match_result is not None else None

                    urban_item = UrbanItem(
                        item["word"],
                        re.sub(r"[!\[]|[!\]]", "**", item["definition"]),
                        re.sub(r"[!\[]|[!\]]", "**", item["example"]),
                        permalink,
                        item["author"],
                        dparser.parse(item["written_on"]),
                    )
                    urban_list.append(urban_item)

                if urban_list != []:
                    embeds = self.urban_embeds(ctx, urban_list)
                    pass
                else:
                    await ctx.send("No results found.")
                    return

        await self.urban_pages(ctx, embeds)

        return


def setup(bot):
    bot.add_cog(Urban(bot))

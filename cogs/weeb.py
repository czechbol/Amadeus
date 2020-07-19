import discord
import requests
from discord.ext import commands
from discord.abc import PrivateChannel

from core import basecog
from core.text import text
from core.config import config
from repository import vote_repo


repository = vote_repo.VoteRepository()


class Weeb(basecog.Basecog):
    """Weeb shit based commands"""

    def __init__(self, bot):
        self.bot = bot

    @classmethod
    def sauce_tags(cls, dic):
        characters, parodies, tags, artists, groups, languages, categories = ([], [], [], [], [], [], [])
        tags = []
        for tag in dic["tags"]:
            if tag["type"] == "character":
                characters.append(tag["name"])
            elif tag["type"] == "parody":
                parodies.append(tag["name"])
            elif tag["type"] == "tag":
                tags.append(tag["name"])
            elif tag["type"] == "artist":
                artists.append(tag["name"])
            elif tag["type"] == "group":
                groups.append(tag["name"])
            elif tag["type"] == "language":
                languages.append(tag["name"])
            elif tag["type"] == "category":
                categories.append(tag["name"])

        characters = ["Characters", ", ".join(str(e) for e in characters)]
        parodies = ["Parodies", ", ".join(str(e) for e in parodies)]
        tags = ["Tags", ", ".join(str(e) for e in tags)]
        artists = ["Artists", ", ".join(str(e) for e in artists)]
        groups = ["Groups", ", ".join(str(e) for e in groups)]
        languages = ["Languages", ", ".join(str(e) for e in languages)]
        categories = ["Categories", ", ".join(str(e) for e in categories)]

        tags = [
            characters,
            parodies,
            tags,
            artists,
            groups,
            languages,
            categories,
        ]
        return tags

    def sauce_embed(self, ctx, dic, BOOK_ID):
        tags = self.sauce_tags(dic)

        url = "https://nhentai.net/g/{BOOK_ID}/".format(BOOK_ID=BOOK_ID)
        if dic["images"]["pages"][0]["t"] == "j":
            cover_url = "https://i.nhentai.net/galleries/{MEDIA_ID}/1.jpg".format(MEDIA_ID=dic["media_id"])
        elif dic["images"]["pages"][0]["t"] == "p":
            cover_url = "https://i.nhentai.net/galleries/{MEDIA_ID}/1.png".format(MEDIA_ID=dic["media_id"])

        title = dic["title"]["pretty"]
        num_pages = dic["num_pages"]

        embed = self.create_embed(
            author=ctx.message.author, title=title, url=url, color=discord.Colour.from_rgb(227, 47, 86)
        )
        embed.set_image(url=cover_url)
        embed.add_field(name="Number of pages", value=num_pages, inline=True)

        for typ, tag in tags:
            if tag != "":
                if typ == "Tags":
                    embed.add_field(name=typ, value=tag, inline=False)
                else:
                    embed.add_field(name=typ, value=tag, inline=True)
        return embed

    def sauce_check(self, message):
        if isinstance(message.channel, PrivateChannel):
            return True
        role = discord.utils.get(message.guild.roles, name="weeb")
        if role in message.author.roles and message.channel.is_nsfw:
            return True
        return False

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command(
        brief=text.get("weeb", "sauce_desc"),
        description=text.get("weeb", "sauce_desc"),
        help=text.fill("weeb", "sauce_help", prefix=config.prefix),
    )
    async def sauce(self, ctx):
        message = ctx.message
        args = message.content.split(" ")

        if not self.sauce_check(message):
            raise commands.MissingPermissions
        else:
            if len(args) != 2:
                await ctx.send(">>> " + text.fill("weeb", "sauce_help", prefix=config.prefix))
                return
            BOOK_ID = args[1]
            async with ctx.typing():
                try:
                    response = requests.get(
                        "https://nhentai.net/api/gallery/{BOOK_ID}".format(BOOK_ID=BOOK_ID)
                    )
                    dic = response.json()
                    response.raise_for_status()

                except requests.HTTPError as http_err:
                    await ctx.send(f"HTTP error occurred: {http_err}")
                except Exception as err:
                    await ctx.send(f"Error occurred: {err}")
                else:
                    # Request was successful
                    embed = self.sauce_embed(ctx, dic, BOOK_ID)

            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if "omae wa mou shindeiru" in message.content.lower():
            await message.channel.send("NANI")


def setup(bot):
    bot.add_cog(Weeb(bot))

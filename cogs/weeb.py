import discord
import requests
from discord.ext import commands

from core import basecog
from core.text import text
from core.config import config
from repository import vote_repo



repository = vote_repo.VoteRepository()


class Weeb(basecog.Basecog):
    """Weeb shit based commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.is_nsfw()
    @commands.has_role("weeb")
    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command(
        brief=text.get("weeb", "sauce_desc"),
        description=text.get("weeb", "sauce_desc"),
        help=text.fill("weeb", "sauce_help", prefix=config.prefix),
    )
    async def sauce(self, ctx):
        message = ctx.message
        args = message.content.split(" ")
        if len(args) != 2:
            await ctx.send(">>> " + text.fill("weeb", "sauce_help", prefix=config.prefix))
            return
        BOOK_ID = args[1]
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
            characters, parodies, tags, artists, groups, languages, categories = (
                [],
                [],
                [],
                [],
                [],
                [],
                [],
            )
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
            url = "https://nhentai.net/g/{BOOK_ID}/".format(BOOK_ID=BOOK_ID)
            if dic["images"]["pages"][0]["t"] == "j":
                cover_url = "https://i.nhentai.net/galleries/{MEDIA_ID}/1.jpg".format(
                    MEDIA_ID=dic["media_id"]
                )
            elif dic["images"]["pages"][0]["t"] == "p":
                cover_url = "https://i.nhentai.net/galleries/{MEDIA_ID}/1.png".format(
                    MEDIA_ID=dic["media_id"]
                )
            title = dic["title"]["pretty"]
            num_pages = dic["num_pages"]
            characters = ", ".join(str(e) for e in characters)
            parodies = ", ".join(str(e) for e in parodies)
            tags = ", ".join(str(e) for e in tags)
            artists = ", ".join(str(e) for e in artists)
            groups = ", ".join(str(e) for e in groups)
            languages = ", ".join(str(e) for e in languages)
            categories = ", ".join(str(e) for e in categories)
            embed = discord.Embed(title=title, url=url, color=discord.Colour.from_rgb(227, 47, 86))
            embed.set_image(url=cover_url)
            embed.add_field(name="Number of pages", value=num_pages, inline=True)
            if characters != "":
                embed.add_field(name="Characters", value=characters, inline=True)
            if parodies != "":
                embed.add_field(name="Parodies", value=parodies, inline=True)
            if tags != "":
                embed.add_field(name="Tags", value=tags, inline=False)
            if artists != "":
                embed.add_field(name="Artists", value=artists, inline=True)
            if groups != "":
                embed.add_field(name="Groups", value=groups, inline=True)
            if languages != "":
                embed.add_field(name="Languages", value=languages, inline=True)
            if categories != "":
                embed.add_field(name="Categories", value=categories, inline=True)
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if "omae wa mou shindeiru" in message.content.lower():
            await message.channel.send("NANI")


def setup(bot):
    bot.add_cog(Weeb(bot))

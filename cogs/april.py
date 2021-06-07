# import datetime
import random

from discord.ext import commands

from core import basecog, check
from repository import emote_repo


repository = emote_repo.EmoteRepository()


class April(basecog.Basecog):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)

    @commands.command(hidden=True)
    @commands.check(check.is_bot_owner)
    async def april_fools(self, ctx):
        guild = ctx.guild
        emojis = list(guild.emojis)
        original_emojis = []
        new_emojis = []
        for emoji in emojis:
            new_emojis.append({"name": emoji.name, "id": emoji.id})
            original_emojis.append({"name": emoji.name, "id": emoji.id})

        print(f"originals: {original_emojis}")
        random.shuffle(new_emojis)
        await self.log(
            level="info",
            message="April fools emote shenanigans start",
        )
        await ctx.send("April fools emote shenanigans start")
        for idx, emoji in enumerate(emojis):
            new_emojis[idx]["id"] = emoji.id
            await self.log(
                level="info",
                message=f"Setting emote \"{emoji.name}\" to april fools name \"{new_emojis[idx]['name']}\"",
            )
            try:
                await emoji.edit(name=new_emojis[idx]["name"])
            except Exception as e:
                print(emoji.name)
                print(e)
        repo = repository.get_all()
        print(repo)
        await self.log(
            level="info",
            message="April fools emote shenanigans finished",
        )
        await ctx.send("April fools emote shenanigans finished")

    @commands.command(hidden=True)
    @commands.check(check.is_bot_owner)
    async def april_revert(self, ctx):
        guild = ctx.guild
        await self.log(
            level="info",
            message="April fools emote revert start",
        )
        await ctx.send("April fools emote revert start")
        for emoji in guild.emojis:
            db_emote = repository.get_id(emoji.id)
            if db_emote is not None:
                await self.log(
                    level="info",
                    message=f'Setting emote "{db_emote.original_name}" back to its original name.',
                )
                await emoji.edit(name=db_emote.original_name)
        await self.log(
            level="info",
            message="April fools revert finished",
        )
        await ctx.send("April fools emote revert finished")


def setup(bot):
    bot.add_cog(April(bot))

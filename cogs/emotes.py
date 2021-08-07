from discord.ext import commands

from core import basecog, check
from repository import emote_repo


repository = emote_repo.EmoteRepository()


class Emotes(basecog.Basecog):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)

    @commands.check(check.is_bot_owner)
    async def emote_setup(self, ctx):
        guild = ctx.guild
        emojis = guild.emojis
        for emoji in emojis:
            repository.add(emoji)
        repo = repository.get_all()
        print(repo)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        for emoji in after:
            for e in before:
                if e.id == emoji.id and e.name != emoji.name:
                    repository.update(emoji)


def setup(bot):
    bot.add_cog(Emotes(bot))

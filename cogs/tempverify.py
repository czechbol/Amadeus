import asyncio
from datetime import datetime
from datetime import timedelta

import discord
from discord.ext import tasks, commands

from core import basecog
from core.config import config
from repository import tempverify_repo


repository = tempverify_repo.TempverifyRepository()


class Tempverify(basecog.Basecog):
    def __init__(self, bot):
        super().__init__(bot)

    @tasks.loop(seconds=10.0)
    async def tempverify_loop(self):
        repo = repository.get_all()
        if repo != []:
            for row in repo:
                duration = row.end_time - datetime.now()
                duration_in_s = duration.total_seconds()
                if row.end_time < datetime.now():
                    await self.unverify(row)
                elif duration_in_s < 10:
                    await self.unverify(row, time=duration_in_s)

    @tempverify_loop.before_loop
    async def before_tempverify_loop(self):
        if not self.bot.is_ready():
            await self.log(level="info", message="Tempverify loop - waiting until ready()")
            await self.bot.wait_until_ready()

    async def unverify_user(self, row, time=None):
        guild = self.bot.get_guild(row.guild_id)
        member = guild.get_member(row.user_id)
        if member is None:
            return

        if time is not None:
            await asyncio.sleep(time)
        await self.log(level="info", message=f"Tempverify ended for {member.name}")

        for role in member.roles:
            try:
                await member.remove_roles(role, reason="Tempverify ended", atomic=True)
            except discord.errors.Forbidden:
                pass
        await asyncio.sleep(2)

        for channel in member.guild.channels:
            user_overw = channel.overwrites_for(member)
            if user_overw:
                await channel.set_permissions(member, overwrite=None)

    async def tempverify_user(self, member):
        guild = self.getGuild()
        if member is None:
            return

        end_date = datetime.now() + timedelta(days=5)
        verify_role = discord.utils.get(guild.roles, id=config.role_verify)
        guest_role = discord.utils.get(guild.roles, name="GUEST")

        await member.add_roles(verify_role, guest_role, reason="tempverify", atomic=True)

        result = repository.add(guild_id=member.guild.id, user_id=member.id, end_time=end_date)
        return result

    @commands.command()
    async def tempverify(self, ctx):

        if not ctx.message.channel.id == config.channel_jail:
            await ctx.send("Příkaz můžeš použít jen v jail.")
        result = await self.tempverify_user(ctx.message.author)
        if result is None:
            await ctx.send("Nemůžeš se dočasně verifikovat více než jednou.")


def setup(bot):
    bot.add_cog(Tempverify(bot))

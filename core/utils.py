import discord
from discord.ext import commands

import git

from core import config


def generate_mention(user_id):
    return "<@" + str(user_id) + ">"


def git_hash():
    repo = git.Repo(search_parent_directories=True)
    return repo.head.object.hexsha


def git_commit_msg():
    repo = git.Repo(search_parent_directories=True)
    return repo.head.commit.message


def git_pull():
    repo = git.Repo(search_parent_directories=True)
    cmd = repo.git
    return cmd.pull()


def str_emoji_id(emoji):
    if isinstance(emoji, int):
        return str(emoji)

    return emoji if isinstance(emoji, str) else str(emoji.id)


def has_role(user, role):
    if not isinstance(user, discord.Member):
        return None

    try:
        int(role)
        return role in [u.id for u in user.roles]
    except ValueError:
        return role.lower() in [u.name.lower() for u in user.roles]
    return


async def notify(ctx: commands.Context, msg: str):
    """Show an embed.

    A skinny version of rubbercog.throwNotification()
    """
    if ctx.message is None:
        return
    if msg is None:
        msg = ""
    embed = discord.Embed(title=ctx.message.content, color=config.color)
    embed.add_field(name="Výsledek", value=msg, inline=False)
    embed.set_footer(text=ctx.author, icon_url=ctx.author.avatar_url)
    await ctx.send(embed=embed, delete_after=config.delay_embed)

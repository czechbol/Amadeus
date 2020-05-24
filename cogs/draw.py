import os
import re
import numpy
import urllib
import graphviz as gz
from typing import Optional
from matplotlib import pyplot as plt
from numpy import arange, meshgrid, sqrt


from sympy.plotting import plot
from sympy import symbols, simplify

import discord
from discord.ext import commands

from core import basecog
from core.text import text
from core.config import config


class Draw(basecog.Basecog):
    """LaTeX and Graph drawing commands"""

    def __init__(self, bot):
        self.bot = bot
        self.replacements = {
            "sin": "numpy.sin",
            "cos": "numpy.cos",
            "exp": "numpy.exp",
            "sqrt": "numpy.sqrt",
            "^": "**",
        }
        self.allowed_words = [
            "x",
            "sin",
            "cos",
            "sqrt",
            "exp",
        ]

    def string2func(self, string):
        """ evaluates the string and returns a function of x """
        # find all words and check if all are allowed:
        for word in re.findall("[a-zA-Z_]+", string):
            if word not in self.allowed_words:
                raise ValueError('"{}" is forbidden to use in math expression'.format(word))

        for old, new in self.replacements.items():
            string = string.replace(old, new)

        def func(x):
            return eval(string)

        return func

    async def get_math_equation(self, equation):
        """
        send the text equasion to the API
        send the result image to channel
        """
        tex2imgURL = "http://www.sciweavers.org/tex2img.php?eq={}&bc=Black&fc=White&im=png&fs=18&ff=arev&edit=0"
        urllib.request.urlretrieve(
            tex2imgURL.format(urllib.parse.quote(equation)), "assets/latex.png"
        )

        return discord.File("assets/latex.png")

    @commands.command(
        help=text.fill("draw", "latex_help", prefix=config.prefix),
        brief=text.get("draw", "latex_desc"),
        description=text.get("draw", "latex_desc"),
    )
    async def latex(self, ctx, *, equation):
        embed = await self.get_math_equation(equation)
        await ctx.send(file=embed)
        os.remove("assets/latex.png")

    @commands.command(
        help=text.fill("draw", "plot_help", prefix=config.prefix),
        brief=text.get("draw", "plot_desc"),
        description=text.get("draw", "plot_desc"),
    )
    async def plot(self, ctx, from_: Optional[int] = -10, to_: Optional[int] = 10, *, inp: str):

        equations = (
            inp.replace("@", "")
            .replace("#", "")
            .replace("'", "")
            .replace("`", "")
            .replace('"', "")
            .split("; ")
        )
        msg = text.get("draw", "plot_err")
        fig = plt.figure(dpi=300)
        ax = fig.add_subplot(1, 1, 1)

        # Move left y-axis and bottim x-axis to centre, passing through (0,0)
        ax.spines["bottom"].set_position("zero")
        ax.spines["left"].set_position("zero")

        # Eliminate upper and right axes
        ax.spines["right"].set_color("none")
        ax.spines["top"].set_color("none")

        # Show ticks in the left and lower axes only
        ax.xaxis.set_tick_params("bottom", direction="inout")
        ax.yaxis.set_tick_params("left", direction="inout")
        successful_eq = 0
        for eq in equations:
            try:
                func = self.string2func(eq)
                x = numpy.linspace(from_, to_, 250)
                plt.plot(x, func(x))
                plt.xlim(from_, to_)
                successful_eq += 1
            except Exception as e:
                msg += "\n" + eq + " - " + str(e)
        if msg != text.get("draw", "plot_err"):
            await ctx.send(msg)
        if successful_eq > 0:
            plt.savefig("assets/plot.png")
            plt.clf()
            await ctx.send(file=discord.File("assets/plot.png"))
            os.remove("assets/plot.png")
        return

    @commands.command(
        name="digraph",
        aliases=("graphviz",),
        help=text.fill("draw", "digraph_help", prefix=config.prefix),
        brief=text.get("draw", "digraph_desc"),
        description=text.get("draw", "digraph_desc"),
    )
    async def digraph(self, ctx, *, equasion):
        """
        input equasion in dishraph format into graphviz
        save the file into assets/graphviz.png
        send the file to channel
        """
        src = gz.Source(equasion, format="png")
        src.render("assets/graphviz", view=False)

        await ctx.send(file=discord.File("assets/graphviz.png"))
        os.remove("assets/graphviz")
        os.remove("assets/graphviz.png")

    def is_graphviz_message(self, body):
        return body.startswith("```digraph") and body.endswith("```") and body.count("\n") >= 2

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        if message is disgraph compatible
        add the execution (play) button
        """
        if not self.is_graphviz_message(message.content):
            return

        if message.author.bot:
            return

        await message.add_reaction("▶")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """
        check if users clicked the play button on executable code
        the bot has to be a reactor on the executable message
        """

        message = reaction.message
        if not self.is_graphviz_message(message.content):
            return

        if message.author.bot or user.bot or message.author != user:
            return

        if str(reaction.emoji) != "▶":
            return

        if self.bot.user not in await reaction.users().flatten():
            return

        ctx = commands.Context(
            prefix=self.bot.command_prefix,
            guild=message.guild,
            channel=message.channel,
            message=message,
            author=user,
        )
        await self.digraph.callback(
            self, ctx, equasion=message.content.strip("` ` `").replace("digraph\n", "", 1),
        )

        await ctx.message.remove_reaction("▶", ctx.author)
        await ctx.message.remove_reaction("▶", self.bot.user)


def setup(bot):
    bot.add_cog(Draw(bot))

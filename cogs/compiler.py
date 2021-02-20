import re
import json
import aiohttp
import asyncio
import discord
from discord.ext import tasks, commands

from core import basecog


class LanguageItem:
    def __init__(self, name: str, compilers: list):
        self.name = name
        self.compilers = compilers

    def __repr__(self):
        return f'<LanguageItem name="{self.name}" compilers="{self.compilers}">'


class CompilerItem:
    def __init__(
        self,
        compiler_option_raw: bool,
        display_compile_command: str,
        display_name: str,
        language: str,
        name: str,
        provider: int,
        runtime_option_raw: bool,
        switches: list,
        templates: list,
        version: str,
    ):
        self.compiler_option_raw = compiler_option_raw
        self.display_compile_command = display_compile_command
        self.display_name = display_name
        self.language = language
        self.name = name
        self.provider = provider
        self.runtime_option_raw = runtime_option_raw
        self.switches = switches
        self.templates = templates
        self.version = version

    def __repr__(self):
        return (
            f'<CompilerItem name="{self.name}" display_name="{self.display_name}" '
            f'language="{self.language}" version="{self.version}" '
            f'compiler_option_raw="{self.compiler_option_raw}" '
            f'display_compile_command="{self.display_compile_command}" '
            f'provider="{self.provider}" runtime_option_raw="{self.runtime_option_raw}" '
            f'switches="{self.switches}" templates="{self.templates}">'
        )


class Compiler(basecog.Basecog):
    """Compiling code"""

    def __init__(self, bot):
        super().__init__(bot)
        self.update_loop.start()
        self.languages = []

    def cog_unload(self):
        self.unverify_loop.cancel()

    @tasks.loop(hours=36)
    async def update_loop(self):
        await self.log(level="info", message="Compiler update start")
        await self.create_list()
        await self.log(level="info", message="Compiler update finished")

    @update_loop.before_loop
    async def before_update_loop(self):
        if not self.bot.is_ready():
            await self.log(level="info", message="Compiler update loop - waiting until ready()")
            await self.bot.wait_until_ready()

    async def create_list(self):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://wandbox.org/api/list.json") as response:
                dic = await response.json()
                response.raise_for_status()

        langs = []

        for item in dic:
            compiler = CompilerItem(
                item["compiler-option-raw"],
                item["display-compile-command"],
                item["display-name"],
                item["language"],
                item["name"],
                item["provider"],
                item["runtime-option-raw"],
                item["switches"],
                item["templates"],
                item["version"],
            )
            if langs is []:
                language = LanguageItem(compiler.language, [compiler])
                langs.append(language)
            else:
                lang = next((x for x in langs if x.name == compiler.language), None)
                if lang is None:
                    lang = LanguageItem(compiler.language, [compiler])
                    langs.append(lang)
                else:
                    if compiler.name in lang.compilers:
                        await self.log(level="info", message=f"Compiler - Load collision: {compiler.name}")
                    else:
                        lang.compilers.append(compiler)
            langs.sort(key=lambda x: x.name, reverse=False)
            self.languages = langs

    def language_embeds(self, ctx, title, lis):
        embed_list = []
        chunks = [lis[i : i + 21] for i in range(0, len(lis), 21)]

        for idx, chunk in enumerate(chunks):
            embed = self.create_embed(author=ctx.message.author, title=title)
            for count, lang in enumerate(chunk):
                embed.add_field(
                    name=f"{count + 1}) {lang.name}", value=f"{len(lang.compilers)} compilers", inline=True
                )

            embed.add_field(
                name="Page",
                value=f"{idx + 1}/{len(chunks)}",
                inline=False,
            )
            embed_list.append(embed)
        return embed_list

    def compiler_embeds(self, ctx, title, lis):
        embed_list = []
        chunks = [lis[i : i + 21] for i in range(0, len(lis), 21)]

        for idx, chunk in enumerate(chunks):
            embed = self.create_embed(author=ctx.message.author, title=title)
            for count, compiler in enumerate(chunk):
                embed.add_field(
                    name=f"{count + 1}) {compiler.name}", value=f"Version: {compiler.version}", inline=True
                )

            embed.add_field(
                name="Page",
                value=f"{idx + 1}/{len(chunks)}",
                inline=False,
            )
            embed_list.append(embed)
        return embed_list

    async def _pages(self, ctx, embeds):
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
                reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=30.0)
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

    @commands.group(name="compiler")
    async def compiler(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command.qualified_name)

    @compiler.command(name="languages")
    async def compiler_languages(self, ctx):
        languages = self.languages
        embeds = self.language_embeds(ctx, "Supported languages", languages)

        await self._pages(ctx, embeds)

        return

    @compiler.command(name="compilers")
    async def compiler_language_compilers(self, ctx, language: str):
        for lang in self.languages:
            if language.lower() in lang.name.lower():
                break
        else:
            await self.log(level="info", message=f"Compiler - compiler not found: {language}")
            return
        compilers = lang.compilers
        embeds = self.compiler_embeds(ctx, "Supported compilers", compilers)

        await self._pages(ctx, embeds)

        return

    @compiler.command(name="run")
    async def compiler_run(self, ctx, compiler_name: str):
        lang = next((x for x in self.languages if compiler_name.lower() in x.name.lower()), None)
        if lang is not None:
            compiler = lang.compilers[0]
        else:
            for lang in self.languages:
                compiler = next((x for x in lang.compilers if compiler_name.lower() == x.name.lower()), None)
                if compiler is not None:
                    break
            else:
                await self.log(level="info", message=f"Compiler - compiler not found: {compiler_name}")
                return

        message = ctx.message
        try:
            code = re.search("```([^`]*)```", message.content).group(1)
        except AttributeError:
            return

        await message.add_reaction("▶️")

        def check(reaction, user):
            return (
                reaction.message.id == message.id
                and (str(reaction.emoji) == "▶️")
                and user.id == message.author.id
            )

        try:
            reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=300.0)
        except asyncio.TimeoutError:
            await message.clear_reactions()
        else:
            await message.clear_reactions()
            await message.add_reaction("✅")
            params = {
                "compiler": compiler.name,
                "code": code,
                "options": "",
                "compiler-option-raw": "",
                "runtime-option-raw": "",
                "save": True,
            }  # TODO add additional functionality

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://wandbox.org/api/compile.json", data=json.dumps(params)
                ) as response:
                    dic = await response.json()
                    response.raise_for_status()

            status = dic["status"]
            try:
                message = dic["program_message"]
            except KeyError:
                message = dic["compiler_error"]
            url = dic["url"]

            embed = self.create_embed(author=ctx.message.author, title="Compilation results")
            embed.add_field(name="Status", value=f"Finished with exit code: {status}", inline=False)
            embed.add_field(name="Program Output", value=f"```{str(message)}```", inline=False)
            embed.add_field(name="URL", value=f"{url}", inline=False)

            await ctx.send(embed=embed)

        return

    @compiler.command(name="template")
    async def compiler_template(self, ctx, compiler_name: str):
        lang = next((x for x in self.languages if compiler_name.lower() in x.name.lower()), None)
        if lang is not None:
            compiler = lang.compilers[0]
        else:
            for lang in self.languages:
                compiler = next((x for x in lang.compilers if compiler_name.lower() == x.name.lower()), None)
                if compiler is not None:
                    break
            else:
                await self.log(level="info", message=f"Compiler - compiler not found: {compiler_name}")
                return

        await ctx.message.add_reaction("✅")

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://wandbox.org/api/template/{compiler.templates[0]}") as response:
                dic = await response.json()
                response.raise_for_status()

        template = dic["code"]

        embed = self.create_embed(author=ctx.message.author, title="Compiler template")
        embed.add_field(name="Language", value=f"{compiler.language}", inline=True)
        embed.add_field(name="Compiler", value=f"{compiler.name}", inline=True)
        embed.add_field(name="Temmplate", value=f"```{str(template)}```", inline=False)

        await ctx.send(embed=embed)

        return


def setup(bot):
    bot.add_cog(Compiler(bot))

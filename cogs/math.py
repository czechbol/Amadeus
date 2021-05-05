from func_timeout import func_timeout, FunctionTimedOut

import gmpy2
from mathcrypto import MathFunctions, MultiplicativeGroup, DHCryptosystem, DHCracker
from discord.ext import commands

from core import basecog


class Math(basecog.Basecog):
    """Some math stuff"""

    def __init__(self, bot):
        super().__init__(bot)

    @commands.group(pass_context=True, name="group")
    async def group(self, ctx):
        """Multiplicative groups stuff"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command.qualified_name)

    @group.command(name="info")
    async def info(self, ctx, group_modulus: int):
        """Information about multiplicative group\n\
            example:\n\
            `!group info 13`\n
            """
        if group_modulus <= 1:
            await ctx.reply("Modulus must be greater than 1!")
            return

        try:
            group = func_timeout(5, MultiplicativeGroup, args=([group_modulus]))
        except FunctionTimedOut:
            await ctx.reply("Took too long, terminating...")
            return

        elements = ", ".join(str(x) for x in group.elements)
        generators = ", ".join(str(x) for x in group.generators)

        embed = self.create_embed(author=ctx.message.author, title="Multiplicative Group")
        embed.add_field(name="Modulo", value=str(group.mod), inline=True)
        embed.add_field(name="Order", value=str(group.order), inline=True)
        if len(elements) > 1018:
            embed.add_field(name="Elements", value="Too many elements to send through Discord", inline=False)
        else:
            embed.add_field(name="Elements", value=f"```{str(elements)}```", inline=False)

        if len(generators) > 1018:
            embed.add_field(
                name="Generators", value="Too many generators to send through Discord", inline=False
            )
        elif generators == "":
            embed.add_field(
                name="Generators", value="No generators found. Perhaps the group is not cyclic.", inline=False
            )
        else:
            embed.add_field(name="Generators", value=f"```{str(generators)}```", inline=False)

        await ctx.send(embed=embed)

    @group.command(name="inverse")
    async def inverse(self, ctx, group_modulus: int, inverse_to: int):
        """Finds inverse of element in group\n\
            example:\n\
            `!group inverse 13 7`\n
            """

        if not group_modulus > 1:
            await ctx.reply("Modulus must be greater than 1!")
            return
        try:
            group = func_timeout(5, MultiplicativeGroup, args=([group_modulus]))
        except FunctionTimedOut:
            await ctx.reply("Took too long, terminating...")
            return

        try:
            inverse = str(group.get_inverse_element(inverse_to))
        except ValueError:
            inverse = "Element does not belong to the group!"

        embed = self.create_embed(author=ctx.message.author, title="Inverse Element")
        embed.add_field(name="Group Modulo", value=str(group.mod), inline=True)
        embed.add_field(name="Group Order", value=str(group.order), inline=True)
        embed.add_field(name=f"Inverse element to {inverse_to}", value=inverse, inline=False)
        await ctx.send(embed=embed)

    @group.command(name="element-order")
    async def element_order(self, ctx, group_modulus: int, element: int):
        """Finds the order of element in group\n\
            example:\n\
            `!group element-order 13 7`\n
            """

        if not group_modulus > 1:
            await ctx.reply("Modulus must be greater than 1!")
            return

        try:
            group = func_timeout(5, MultiplicativeGroup, args=([group_modulus]))
        except FunctionTimedOut:
            await ctx.reply("Took too long, terminating...")
            return

        try:
            try:
                order = str(func_timeout(5, group.get_element_order, args=([element])))
            except ValueError:
                order = "Element does not belong to the group!"
        except FunctionTimedOut:
            await ctx.reply("Took too long, terminating...")
            return

        embed = self.create_embed(author=ctx.message.author, title="Order of Element")
        embed.add_field(name="Group Modulo", value=str(group.mod), inline=True)
        embed.add_field(name="Group Order", value=str(group.order), inline=True)
        embed.add_field(name=f"Order of {element}", value=order, inline=False)
        await ctx.send(embed=embed)

    @commands.group(pass_context=True, name="math")
    async def math(self, ctx):
        """Useful crypto math functions"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command.qualified_name)

    @math.command(name="is-prime")
    async def is_prime(self, ctx, num: int):
        """Checks if number is prime
        Uses 25 rounds of Miller-Rabin primality test.
        `!math is-prime 125863`\n
        """

        try:
            result = func_timeout(5, gmpy2.is_prime, args=([num]))
        except FunctionTimedOut:
            await ctx.reply("Took too long, terminating...")
            return

        embed = self.create_embed(
            author=ctx.message.author, title=f"Is {num} prime?", description=str(result)
        )
        if len(str(num)) > 256:
            embed.title = "Is this number prime?"
            await ctx.reply(embed=embed)
        else:
            await ctx.send(embed=embed)

    @math.command(name="factorize")
    async def factorize(self, ctx, num: int):
        """Factorization of a number\n\
            example:\n\
            `!math factorize 362880`\n
            """
        if not num > 1:
            await ctx.reply("Are you trying to factorize a number smaller than 2?")
            return
        try:
            result = func_timeout(5, MathFunctions.factorize, args=([num]))
        except FunctionTimedOut:
            await ctx.reply("Took too long, terminating...")
            return

        factors = ", ".join(str(x) for x in result)

        embed = self.create_embed(author=ctx.message.author, title=f"Factors of {num}:", description=factors)
        if len(factors) > 2048:
            embed.description = "String too long for Discord"
        if len(str(num)) > 256:
            embed.title = "Factors of this number."
            await ctx.reply(embed=embed)
        else:
            await ctx.send(embed=embed)

    @math.command(name="phi")
    async def phi(self, ctx, num: int):
        """Euler's Totient function\n\
            example:\n\
            `!math phi 12`\n
            """
        try:
            result = func_timeout(5, MathFunctions.phi, args=([num]))
        except FunctionTimedOut:
            await ctx.reply("Took too long, terminating...")
            return

        embed = self.create_embed(
            author=ctx.message.author, title=f"Euler's Totient function of {num}:", description=result
        )
        if len(str(result)) > 2048:
            embed.description = "String too long for Discord"
        if len(f"Euler's Totient function of {num}:") > 256:
            embed.title = "Factors of this number."
            await ctx.reply(embed=embed)
        else:
            await ctx.send(embed=embed)

    @math.command(name="fermat")
    async def fermat(self, ctx, num: int, test_number: int = None):
        """Fermat's primality test\n\
            tests if number is prime\n\n\
            example:\n\
            `!math fermat 10` for automated test (tests 5 rounds of FPT)\n\
            `!math fermat 10 3` for manual test (tests with testing number 3)\n
            """
        if test_number is not None:
            is_prime, result = MathFunctions.fermat_prime_test_manual(num, test_number, verbose=True)
        else:
            is_prime, result = MathFunctions.fermat_prime_test_auto(num, verbose=True)
        result_string = ""
        for item in result:
            result_string += f"\n    tested with: {item[0]}, result = {item[1]}"

        embed = self.create_embed(author=ctx.message.author, title=f"Fermat's primality test of {num}:")
        if is_prime and test_number is None:
            embed.add_field(
                name="Result:",
                value=f"{num} is probably prime!\nTried rounds:\n{result_string}",
                inline=False,
            )
        elif test_number is None:
            embed.add_field(
                name="Result:",
                value=f"{num} is not prime! Result must be 1 for all tries.\n{result_string}",
                inline=False,
            )
        elif is_prime:
            embed.add_field(
                name="Result:",
                value=f"{num} might be prime!\n{result_string}\n\n But be careful, one test element might not be enough to test primality with enough probablility.",
                inline=False,
            )
        else:
            embed.add_field(
                name="Result:",
                value=f"{num} is not prime! Result must be 1 for all tries.\n{result_string}",
                inline=False,
            )
        await ctx.send(embed=embed)

    @math.command(name="euclid")
    async def euclid(self, ctx, num_a: int, num_b: int):
        """Euclid's greatest common divisor\n\
            finds GCD of two numbers\n\n\
            example:\n\
            `!math euclid 10 15`\n
            """

        try:
            result = func_timeout(5, MathFunctions.euclid_gcd, args=([num_a, num_b]))
        except FunctionTimedOut:
            await ctx.reply("Took too long, terminating...")
            return

        embed = self.create_embed(
            author=ctx.message.author,
            title=f"Euclid's greatest common divisor of {num_a} and {num_b}:",
            description=str(result),
        )
        await ctx.send(embed=embed)

    @math.command(name="crt")
    async def crt(self, ctx, string: str):
        """Chinese Remainder Theorem calculation\n\
            finds x that works for all congruences\n\n\
            if you have:\n\
                `x ≡ 8 mod 9`\n\
                `x ≡ 3 mod 5`\n\
            format it like this:\n\
            `!math crt \"(8,9), (3, 5)\"`\n
            """
        string = string.replace(" ", "")
        strs = string.replace("(", "").split("),")

        try:
            lists = [list(map(int, s.replace(")", "").split(","))) for s in strs]
        except ValueError:
            await ctx.reply("You didn't format it right, see help.")
            return
        crt_list = []
        desc = ""
        for item in lists:
            if len(item) == 2:
                crt_list.append([item[0], item[1]])
                desc += f"\nX ≡ {item[0]} (mod {item[1]})"
            else:
                ctx.reply("You didn't format it right, see help.")
                return

        try:
            result = func_timeout(5, MathFunctions.crt, args=([crt_list]))
        except FunctionTimedOut:
            await ctx.reply("Took too long, terminating...")
            return

        embed = self.create_embed(
            author=ctx.message.author,
            title="Chinese remainder theorem",
            description=f"Set by:\n{desc}",
        )
        embed.add_field(
            name="Result:",
            value=f"{result}",
            inline=False,
        )
        await ctx.send(embed=embed)

    @math.command(name="eea")
    async def eea(self, ctx, modulus: int, number: int):
        """Get multiplicative using Extended Euclidean Algorithm\n\
            example:
            `!math eea 12 5`"""
        result = MathFunctions.eea(modulus, number)

        embed = self.create_embed(
            author=ctx.message.author,
            title="Extended Euclidean Algorithm",
            description=f"```{result}```",
        )
        await ctx.send(embed=embed)

    @commands.group(pass_context=True, name="crypto")
    async def crypto(self, ctx):
        """Crypto protocols implementation"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command.qualified_name)

    @crypto.command(name="compute-dh")
    async def compute_dh(self, ctx, prime: int, generator: int):
        """Calculate the Diffie Hellman protocol\n\
            example:\n\
            `!crypto compute-dh prime generator` where generator is random number from 1 to (prime - 1)\n\
            `!crypto compute-dh 1723 1589`"""
        try:
            prime_is_prime = gmpy2.is_prime(prime)
        except FunctionTimedOut:
            await ctx.reply("Took too long, terminating...")
            return
        if not prime_is_prime:
            await ctx.reply("First number needs to be prime!")
            return

        result = DHCryptosystem.generate_from(prime, generator)

        alice_secret = result["alice_secret"]
        bob_secret = result["bob_secret"]
        alice_sends = result["alice_sends"]
        bob_sends = result["bob_sends"]
        alices_key = result["alices_key"]
        bobs_key = result["bobs_key"]

        embed = self.create_embed(
            author=ctx.message.author,
            title="Diffie-Hellman Protocol",
            description=f"Set by:\nprime: {prime}\ngenerator: {generator}",
        )
        embed.add_field(
            name="Secrets:",
            value=f"alice_secret: {alice_secret}\nbob_secret: {bob_secret}",
            inline=True,
        )
        embed.add_field(
            name="Sent through unencrypted:",
            value=f"alice_sends: {alice_sends}\nbob_sends: {bob_sends}",
            inline=True,
        )
        embed.add_field(
            name="Calculated keys:",
            value=f"alices_key: {alices_key}\nbobs_key: {bobs_key}",
            inline=True,
        )
        await ctx.send(embed=embed)

    @crypto.command(name="crack-dh")
    async def crack_dh(self, ctx, prime: int, generator: int, alice_sends: int, bob_sends: int):
        """Crack the Diffie Hellman protocol\n\
            example:\n\
            `!crypto compute-dh 1723 1589 1360 955`"""
        crack_me = DHCryptosystem(prime, generator, alice_sends, bob_sends)
        try:
            result = DHCracker.baby_step(crack_me)
        except MemoryError:
            await ctx.reply("Ate too much memory, terminating...")
            return
        embed = self.create_embed(
            author=ctx.message.author,
            title="Diffie-Hellman Protocol",
            description=f"Set by:\nprime: {prime}\ngenerator: {generator}",
        )
        embed.add_field(
            name="Sent through unencrypted:",
            value=f"alice_sends: {alice_sends}\nbob_sends: {bob_sends}",
            inline=True,
        )
        embed.add_field(
            name="Cracked key:",
            value=f"{result}",
            inline=False,
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Math(bot))

import math
import time
import psutil
import random
from itertools import count, islice

from discord.ext import commands

from core import basecog


class Funcs:
    primes = []

    @classmethod
    def is_prime(cls, num: int):
        if num < 2:
            return False
        timeout = time.time() + 5

        for number in islice(count(2), int(math.sqrt(num) - 1)):
            if time.time() > timeout:
                raise TimeoutError
            if num % number == 0:
                return False
        return True

    @classmethod
    def factorize(cls, num: int):
        factors = []
        timeout = time.time() + 5

        while (num % 2) == 0:
            factors.append(2)  # supposing you want multiple factors repeated
            num //= 2
        for number in islice(count(3, 2), int((math.sqrt(num) / 2) - 1)):
            if time.time() > timeout:
                raise TimeoutError
            while (num % number) == 0:
                factors.append(number)  # supposing you want multiple factors repeated
                num //= number

        if num > 1:
            factors.append(num)
        return factors

    @classmethod
    def phi(cls, num: int):
        if cls.is_prime(num):
            return num - 1

        result = 0
        timeout = time.time() + 5
        for i in range(1, num):
            if time.time() > timeout:
                raise TimeoutError
            if math.gcd(i, num) == 1:
                result += 1
        return result

    @classmethod
    def fermat_prime_test(cls, num: int, tester: int = None):
        if tester is None:
            if num - 1 < 5:
                rounds = num - 1
            else:
                rounds = 5

                result = []
            for x in range(rounds):
                tester = random.randint(2, num - 2)  # nosec
                res = pow(tester, num - 1, num)
                result.append({"testvalue": tester, "result": res})

        else:
            res = pow(tester, num - 1, num)
            result = [{"testvalue": tester, "result": res}]
        return result

    @classmethod
    def euclid_gcd(cls, num_a: int, num_b: int, timeout):
        if time.time() > timeout:
            raise TimeoutError
        if num_a == 0:
            return num_b
        return cls.euclid_gcd(num_b % num_a, num_a, timeout)

    @classmethod
    def crt(cls, dic):
        M = 1
        temp = 0

        moduli = []
        for item in dic:
            if moduli == []:
                moduli.append(item["modulus"])
                M *= item["modulus"]

            for num in moduli:
                if math.gcd(num, item["modulus"]) != 1:
                    break
            else:
                moduli.append(item["modulus"])
                M *= item["modulus"]

        for item in dic:
            N = int(M / item["modulus"])
            L = pow(N, Funcs.phi(item["modulus"]) - 1, item["modulus"])
            W = (L * N) % M
            temp += item["result"] * W
        return temp % M

    @classmethod
    def eea(cls, n: int, x: int):
        # Blame Cauchy, I didn't program this :kek:

        table = []

        # get left side
        table.append([n, 0])

        left = x
        while left > 0:
            table.append([left, table[-1][0] // left])

            left = table[-2][0] - (left * table[-1][1])
        table.append([0, 0])

        # get right side
        for i, row in enumerate(table):
            # do not include the lowest row
            if i == 0:
                table[-i - 1].append(0)
            # add 0, 1 upwards
            elif i == 1:
                table[-i - 1].append(0)
            elif i == 2:
                table[-i - 1].append(1)
            # compute
            else:
                a = table[-i][1]
                b = table[-i][2]
                try:
                    c = table[-i + 1][2]
                except IndexError:
                    # top row
                    c = 0
                table[-i - 1].append(a * b + c)

        result = []

        for i in range(len(table)):
            if i == 0:
                # results row
                result.append(
                    [
                        f"n = {table[i][0]}",
                        "",
                        f"{table[i][2]} = {table[i+1][1]}*{table[i+1][2]}+{table[i+2][2]}",
                    ]
                )
                continue
            if i == 1:
                # seeked variable row
                result.append(
                    [
                        f"x = {table[i][0]}",
                        f"{table[i][1]} = ⌊{table[i-1][0]}/{table[i][0]}⌋",
                        f"{table[i][2]} = {table[i+1][1]}*{table[i+1][2]}+{table[i+2][2]}",
                    ]
                )
                continue
            if i == len(table) - 3:
                # row ends with "1"
                result.append(
                    [
                        f"{table[i][0]} = {table[i-2][0]}-({table[i-1][0]}*{table[i-1][1]})",
                        f"{table[i][1]} = ⌊{table[i-1][0]}/{table[i][0]}⌋",
                        "1",
                    ]
                )
                continue
            if i == len(table) - 2:
                # row ends with "0"
                result.append(
                    [
                        f"{table[i][0]} = {table[i-2][0]}-({table[i-1][0]}*{table[i-1][1]})",
                        f"{table[i][1]} = ⌊{table[i-1][0]}/{table[i][0]}⌋",
                        "0",
                    ]
                )
                continue
            if i == len(table) - 1:
                # left number is zero
                result.append(
                    [
                        f"{table[i][0]} = {table[i-2][0]}-({table[i-1][0]}*{table[i-1][1]})",
                        "",
                        "",
                    ]
                )
                continue
            # normal row
            result.append(
                [
                    f"{table[i][0]} = {table[i-2][0]}-({table[i-1][0]}*{table[i-1][1]})",
                    f"{table[i][1]} = ⌊{table[i-1][0]}/{table[i][0]}⌋",
                    f"{table[i][2]} = {table[i+1][1]}*{table[i+1][2]}+{table[i+2][2]}",
                ]
            )
        res = table[0][2]
        flip = False
        if (res * x) % n != 1:
            res = -res % n
            flip = True

        if flip:
            eq = f"-{res} mod {n} = {-res % n}"
        else:
            eq = str(res)

        width = []
        for i in range(3):
            width.append(max(len(s[i]) for s in result))
        lines = ""
        for row in result:
            line = "  ".join(row[i].ljust(width[i]) for i in range(3))
            lines += f"\n{line}"
        lines += "\n"
        lines += f"\nThe result is {eq}."
        return lines


class MultiplicativeGroup(object):
    def __init__(self, mod=None):
        self.mod = mod
        self.elements = self.generate_elements(mod)
        self.order = len(self.elements)
        self.generators = self.get_generators()

    def __repr__(self):
        return f'<MultiplicativeGroup mod="{self.mod}" order="{self.order}" elements="{self.elements}" generators="{self.generators}">'

    def generate_elements(self, mod: int):
        elements = []
        timeout = time.time() + 5
        for i in range(1, mod):
            if time.time() > timeout:
                raise TimeoutError
            if math.gcd(i, mod) == 1:
                elements.append(i)
        return elements

    def get_element_order(self, element):
        if element not in self.elements:
            raise ValueError
        s = set()
        for exp in range(len(self.elements)):
            s.add(element ** exp % self.mod)
        return len(s)

    def get_inverse(self, element: int):
        if element not in self.elements:
            raise ValueError
        inverse = pow(element, Funcs.phi(self.mod) - 1, self.mod)
        return inverse

    def get_generators(self):
        phi = Funcs.phi(self.mod)
        phi_factors = Funcs.factorize(phi)
        cleaned_factors = []
        for i in phi_factors:
            if i not in cleaned_factors:
                cleaned_factors.append(i)

        generators = []
        for element in self.elements:
            for factor in cleaned_factors:
                if pow(element, int(phi / factor), self.mod) == 1:
                    break
            else:
                generators.append(element)
        return generators


class Crypto:
    @classmethod
    def calculate_dh(cls, prime, generator):
        alice_secret: int = random.randint(1, prime)  # nosec # only Alice knows this
        bob_secret: int = random.randint(1, prime)  # nosec # only Bob knows this
        alice_sends = pow(generator, alice_secret, prime)
        bob_sends = pow(generator, bob_secret, prime)
        alices_key = pow(bob_sends, alice_secret, prime)
        bobs_key = pow(alice_sends, bob_secret, prime)
        return {
            "prime": prime,
            "generator": generator,
            "alice_secret": alice_secret,
            "bob_secret": bob_secret,
            "alice_sends": alice_sends,
            "bob_sends": bob_sends,
            "alices_key": alices_key,
            "bobs_key": bobs_key,
        }

    @classmethod
    def crack_dh(cls, prime, generator, alice_sends, bob_sends):
        N = 1 + int(math.sqrt(prime))

        baby_steps_tabulka = {}
        baby_step = 1
        for i in range(N + 1):
            if psutil.virtual_memory().available * 100 / psutil.virtual_memory().total < 10:
                raise MemoryError
            baby_steps_tabulka[baby_step] = i
            baby_step = baby_step * generator % prime

        inverzni_k_N = pow(generator, (prime - 2) * N, prime)
        giant_step = random.choice([alice_sends, bob_sends])  # nosec
        for j in range(N + 1):
            if giant_step in baby_steps_tabulka:
                temp = j * N + baby_steps_tabulka[giant_step]
                log = pow(generator, temp, prime)
                if log == alice_sends:
                    cracked_key = pow(bob_sends, temp, prime)
                if log == bob_sends:
                    cracked_key = pow(alice_sends, temp, prime)

                return cracked_key
            else:
                giant_step = giant_step * inverzni_k_N % prime
        return "No Match"


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
            group = MultiplicativeGroup(group_modulus)
        except TimeoutError:
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
            group = MultiplicativeGroup(group_modulus)
        except TimeoutError:
            await ctx.reply("Took too long, terminating...")
            return

        group = MultiplicativeGroup(group_modulus)
        try:
            inverse = str(group.get_inverse(inverse_to))
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
            group = MultiplicativeGroup(group_modulus)
        except TimeoutError:
            await ctx.reply("Took too long, terminating...")
            return

        group = MultiplicativeGroup(group_modulus)
        try:
            order = str(group.get_element_order(element))
        except ValueError:
            order = "Element does not belong to the group!"

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
        """Checks if number is prime\n\
            similar to `math fermat` but will result in 100% correct result, slower tho
            example:\n\
            `!math is-prime 125863`\n
            """

        try:
            result = Funcs.is_prime(num)
        except TimeoutError:
            await ctx.reply("Took too long, terminating...")
            return

        embed = self.create_embed(
            author=ctx.message.author, title=f"Is {num} prime?", description=str(result)
        )
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
            result = Funcs.factorize(num)
        except TimeoutError:
            await ctx.reply("Took too long, terminating...")
            return

        factors = ", ".join(str(x) for x in result)

        embed = self.create_embed(author=ctx.message.author, title=f"Factors of {num}:", description=factors)
        await ctx.send(embed=embed)

    @math.command(name="phi")
    async def phi(self, ctx, num: int):
        """Euler's Totient function\n\
            example:\n\
            `!math phi 12`\n
            """
        try:
            result = Funcs.phi(num)
        except TimeoutError:
            await ctx.reply("Took too long, terminating...")
            return

        embed = self.create_embed(
            author=ctx.message.author, title=f"Euler's Totient function of {num}:", description=result
        )
        await ctx.send(embed=embed)

    @math.command(name="fermat")
    async def fermat(self, ctx, num: int, test_number: int = None):
        """Fermat's primality test\n\
            tests if number is prime\n\n\
            example:\n\
            `!math fermat 10` for automated test (tests 5 rounds of FPT)\n\
            `!math fermat 10 3` for manual test (tests with testing number 3)\n
            """
        result = Funcs.fermat_prime_test(num, test_number)
        result_string = ""
        is_prime = None
        for item in result:
            testvalue = item["testvalue"]
            result = item["result"]
            result_string += f"\n    tested with: {testvalue}, result = {result}"
            if item["result"] != 1:
                is_prime = False
        if is_prime is None:
            is_prime = True

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
            timeout = time.time() + 5
            result = Funcs.euclid_gcd(num_a, num_b, timeout)
        except TimeoutError:
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
                crt_list.append({"result": item[0], "modulus": item[1]})
                desc += f"\nX ≡ {item[0]} (mod {item[1]})"

            else:
                ctx.reply("You didn't format it right, see help.")
                return
        try:
            result = Funcs.crt(crt_list)
        except TimeoutError:
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
        result = Funcs.eea(modulus, number)

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
            prime_is_prime = Funcs.is_prime(prime)
        except TimeoutError:
            await ctx.reply("Took too long, terminating...")
            return
        if not prime_is_prime:
            await ctx.reply("First number needs to be prime!")
            return

        result = Crypto.calculate_dh(prime, generator)

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
        try:
            result = Crypto.crack_dh(prime, generator, alice_sends, bob_sends)
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

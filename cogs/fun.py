import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import random
import logging
import config

logger = logging.getLogger(__name__)

class Fun(commands.Cog):
    """Fun commands - praise, scold, urban dictionary, and more"""

    def __init__(self, bot):
        self.bot = bot
        self.session = None

        self.praise_messages = [
            "{user}, you're doing amazing! Keep it up!",
            "Great job, {user}! Yuno is proud of you!",
            "{user} is absolutely wonderful!",
            "You're the best, {user}!",
            "{user}, you make everything better!",
            "Ara ara~ {user}, you're so talented!",
            "{user} deserves all the headpats!",
            "Good job, {user}! You're a star!",
            "{user} is precious and must be protected!",
            "Yuno believes in you, {user}!"
        ]

        self.scold_messages = [
            "{user}, you disappointed Yuno...",
            "Bad {user}! No headpats for you!",
            "{user}, Yuno is watching... and judging.",
            "Tsk tsk, {user}. Do better.",
            "{user}, you made Yuno sad...",
            "Ara ara~ {user}, that wasn't very nice.",
            "{user} needs to reflect on their actions!",
            "Yuno is not happy with you, {user}!",
            "{user}, consider this your final warning!",
            "Bad! Bad {user}!"
        ]

    async def cog_load(self):
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        if self.session:
            await self.session.close()

    # === PRAISE ===
    @commands.command(name="praise")
    async def praise(self, ctx, *, user: discord.Member = None):
        """Praise someone (or yourself)

        Usage: ?praise @User
        """
        user = user or ctx.author
        message = random.choice(self.praise_messages).format(user=user.display_name)

        embed = discord.Embed(
            description=message,
            color=config.COLOR_SUCCESS
        )
        embed.set_author(name="Praise!", icon_url=user.display_avatar.url)

        # Try to get a happy anime gif
        try:
            async with self.session.get("https://nekos.life/api/v2/img/pat") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    embed.set_image(url=data.get("url"))
        except Exception:
            pass

        await ctx.send(embed=embed)

    # === SCOLD ===
    @commands.command(name="scold")
    async def scold(self, ctx, *, user: discord.Member = None):
        """Scold someone

        Usage: ?scold @User
        """
        if user is None:
            return await ctx.send("You need to specify someone to scold!")

        if user == self.bot.user:
            return await ctx.send("Y-you can't scold Yuno!")

        message = random.choice(self.scold_messages).format(user=user.display_name)

        embed = discord.Embed(
            description=message,
            color=config.COLOR_ERROR
        )
        embed.set_author(name="Scolded!", icon_url=user.display_avatar.url)

        # Try to get an angry/pout anime gif
        try:
            async with self.session.get("https://nekos.life/api/v2/img/pout") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    embed.set_image(url=data.get("url"))
        except Exception:
            pass

        await ctx.send(embed=embed)

    # === URBAN DICTIONARY ===
    @commands.command(name="urban", aliases=["ud", "define"])
    async def urban(self, ctx, *, term: str):
        """Look up a term on Urban Dictionary

        Usage: ?urban yandere
        """
        try:
            async with self.session.get(
                "https://api.urbandictionary.com/v0/define",
                params={"term": term}
            ) as resp:
                if resp.status != 200:
                    return await ctx.send("Could not reach Urban Dictionary.")
                data = await resp.json()
        except Exception as e:
            logger.error(f"Urban Dictionary error: {e}")
            return await ctx.send("Error looking up definition.")

        definitions = data.get("list", [])
        if not definitions:
            return await ctx.send(f"No definition found for `{term}`")

        # Get top definition
        top = definitions[0]

        definition = top.get("definition", "No definition")[:1024]
        example = top.get("example", "")[:1024]

        # Clean up Urban Dictionary formatting (remove brackets)
        definition = definition.replace("[", "").replace("]", "")
        example = example.replace("[", "").replace("]", "")

        embed = discord.Embed(
            title=f"Urban Dictionary: {top.get('word', term)}",
            url=top.get("permalink"),
            color=config.COLOR_INFO
        )
        embed.add_field(name="Definition", value=definition or "None", inline=False)
        if example:
            embed.add_field(name="Example", value=f"*{example}*", inline=False)

        thumbs_up = top.get("thumbs_up", 0)
        thumbs_down = top.get("thumbs_down", 0)
        embed.set_footer(text=f" {thumbs_up} |  {thumbs_down}")

        await ctx.send(embed=embed)

    # === HUG ===
    @commands.command(name="hug")
    async def hug(self, ctx, *, user: discord.Member = None):
        """Hug someone

        Usage: ?hug @User
        """
        if user is None:
            return await ctx.send("Who do you want to hug?")

        if user == ctx.author:
            message = f"{ctx.author.display_name} hugs themselves... Yuno will hug you!"
        elif user == self.bot.user:
            message = f"Yuno hugs {ctx.author.display_name} back!"
        else:
            message = f"{ctx.author.display_name} hugs {user.display_name}!"

        embed = discord.Embed(
            description=message,
            color=config.COLOR_PRIMARY
        )

        try:
            async with self.session.get("https://nekos.life/api/v2/img/hug") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    embed.set_image(url=data.get("url"))
        except Exception:
            pass

        await ctx.send(embed=embed)

    # === SLAP ===
    @commands.command(name="slap")
    async def slap(self, ctx, *, user: discord.Member = None):
        """Slap someone

        Usage: ?slap @User
        """
        if user is None:
            return await ctx.send("Who do you want to slap?")

        if user == ctx.author:
            message = f"{ctx.author.display_name} slaps themselves... why?"
        elif user == self.bot.user:
            message = f"You can't slap Yuno! *slaps {ctx.author.display_name} instead*"
        else:
            message = f"{ctx.author.display_name} slaps {user.display_name}!"

        embed = discord.Embed(
            description=message,
            color=config.COLOR_WARNING
        )

        try:
            async with self.session.get("https://nekos.life/api/v2/img/slap") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    embed.set_image(url=data.get("url"))
        except Exception:
            pass

        await ctx.send(embed=embed)

    # === KISS ===
    @commands.command(name="kiss")
    async def kiss(self, ctx, *, user: discord.Member = None):
        """Kiss someone

        Usage: ?kiss @User
        """
        if user is None:
            return await ctx.send("Who do you want to kiss?")

        if user == ctx.author:
            message = f"{ctx.author.display_name} kisses the mirror!"
        elif user == self.bot.user:
            message = f"K-kyaa! {ctx.author.display_name} kissed Yuno!"
        else:
            message = f"{ctx.author.display_name} kisses {user.display_name}!"

        embed = discord.Embed(
            description=message,
            color=config.COLOR_PRIMARY
        )

        try:
            async with self.session.get("https://nekos.life/api/v2/img/kiss") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    embed.set_image(url=data.get("url"))
        except Exception:
            pass

        await ctx.send(embed=embed)

    # === CUDDLE ===
    @commands.command(name="cuddle")
    async def cuddle(self, ctx, *, user: discord.Member = None):
        """Cuddle with someone

        Usage: ?cuddle @User
        """
        if user is None:
            return await ctx.send("Who do you want to cuddle?")

        if user == ctx.author:
            message = f"{ctx.author.display_name} cuddles with a pillow..."
        elif user == self.bot.user:
            message = f"Yuno cuddles with {ctx.author.display_name}!"
        else:
            message = f"{ctx.author.display_name} cuddles with {user.display_name}!"

        embed = discord.Embed(
            description=message,
            color=config.COLOR_PRIMARY
        )

        try:
            async with self.session.get("https://nekos.life/api/v2/img/cuddle") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    embed.set_image(url=data.get("url"))
        except Exception:
            pass

        await ctx.send(embed=embed)

    # === FEED ===
    @commands.command(name="feed")
    async def feed(self, ctx, *, user: discord.Member = None):
        """Feed someone

        Usage: ?feed @User
        """
        if user is None:
            return await ctx.send("Who do you want to feed?")

        if user == ctx.author:
            message = f"{ctx.author.display_name} feeds themselves!"
        elif user == self.bot.user:
            message = f"Thank you for feeding Yuno!"
        else:
            message = f"{ctx.author.display_name} feeds {user.display_name}!"

        embed = discord.Embed(
            description=message,
            color=config.COLOR_SUCCESS
        )

        try:
            async with self.session.get("https://nekos.life/api/v2/img/feed") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    embed.set_image(url=data.get("url"))
        except Exception:
            pass

        await ctx.send(embed=embed)

    # === POKE ===
    @commands.command(name="poke")
    async def poke(self, ctx, *, user: discord.Member = None):
        """Poke someone

        Usage: ?poke @User
        """
        if user is None:
            return await ctx.send("Who do you want to poke?")

        if user == ctx.author:
            message = f"{ctx.author.display_name} pokes themselves..."
        elif user == self.bot.user:
            message = f"*poke* What is it, {ctx.author.display_name}?"
        else:
            message = f"{ctx.author.display_name} pokes {user.display_name}!"

        embed = discord.Embed(
            description=message,
            color=config.COLOR_INFO
        )

        try:
            async with self.session.get("https://nekos.life/api/v2/img/poke") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    embed.set_image(url=data.get("url"))
        except Exception:
            pass

        await ctx.send(embed=embed)

    # === TICKLE ===
    @commands.command(name="tickle")
    async def tickle(self, ctx, *, user: discord.Member = None):
        """Tickle someone

        Usage: ?tickle @User
        """
        if user is None:
            return await ctx.send("Who do you want to tickle?")

        if user == ctx.author:
            message = f"{ctx.author.display_name} tickles themselves... how?"
        elif user == self.bot.user:
            message = f"Ahaha! S-stop it, {ctx.author.display_name}!"
        else:
            message = f"{ctx.author.display_name} tickles {user.display_name}!"

        embed = discord.Embed(
            description=message,
            color=config.COLOR_SUCCESS
        )

        try:
            async with self.session.get("https://nekos.life/api/v2/img/tickle") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    embed.set_image(url=data.get("url"))
        except Exception:
            pass

        await ctx.send(embed=embed)

    # === SLASH COMMANDS ===
    @app_commands.command(name="urban", description="Look up a term on Urban Dictionary")
    @app_commands.describe(term="The term to look up")
    async def slash_urban(self, interaction: discord.Interaction, term: str):
        """Slash command for urban dictionary"""
        await interaction.response.defer()

        try:
            async with self.session.get(
                "https://api.urbandictionary.com/v0/define",
                params={"term": term}
            ) as resp:
                if resp.status != 200:
                    return await interaction.followup.send("Could not reach Urban Dictionary.")
                data = await resp.json()
        except Exception:
            return await interaction.followup.send("Error looking up definition.")

        definitions = data.get("list", [])
        if not definitions:
            return await interaction.followup.send(f"No definition found for `{term}`")

        top = definitions[0]
        definition = top.get("definition", "No definition")[:1024]
        definition = definition.replace("[", "").replace("]", "")

        embed = discord.Embed(
            title=f"Urban Dictionary: {top.get('word', term)}",
            url=top.get("permalink"),
            color=config.COLOR_INFO
        )
        embed.add_field(name="Definition", value=definition, inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="hug", description="Hug someone")
    @app_commands.describe(user="The person to hug")
    async def slash_hug(self, interaction: discord.Interaction, user: discord.Member):
        """Slash command for hug"""
        if user == interaction.user:
            message = f"{interaction.user.display_name} hugs themselves..."
        else:
            message = f"{interaction.user.display_name} hugs {user.display_name}!"

        embed = discord.Embed(description=message, color=config.COLOR_PRIMARY)

        try:
            async with self.session.get("https://nekos.life/api/v2/img/hug") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    embed.set_image(url=data.get("url"))
        except Exception:
            pass

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Fun(bot))
    logger.info("Fun cog loaded")

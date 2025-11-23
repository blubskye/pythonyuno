import discord
from discord.ext import commands

class AGPL(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="source",
        aliases=["src", "code", "github", "repo", "opensource"]
    )
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def source(self, ctx):
        """AGPL §13 compliance — sends source code link, tries DM first"""
        url = "https://github.com/blubskye/pythonyuno"
        embed = discord.Embed(
            title="Yuno • Open Source",
            description=(
                "This bot is licensed under the **GNU AGPL-3.0**.\n"
                "You are free to view, use, modify, and redistribute it — "
                "as long as you share your changes under the same license.\n\n"
                f"**Source Code:** [github.com/blubskye/pythonyuno]({url})"
            ),
            color=0xff003d,
            url=url
        )
        embed.set_thumbnail(url="https://www.gnu.org/graphics/agplv3-155x51.png")
        embed.set_footer(text="Free Software • Free as in Freedom")
        embed.timestamp = discord.utils.utcnow()

        # Try DM first
        try:
            await ctx.author.send(embed=embed)
            if ctx.guild:
                await ctx.message.add_reaction("Checkmark")  # Success
        except discord.Forbidden:
            # DMs blocked — send in channel
            try:
                await ctx.send(
                    f"{ctx.author.mention} I couldn't send you a DM (your privacy settings block it).\n"
                    "Here’s the source code publicly:",
                    embed=embed
                )
            except:
                # Absolute last resort
                await ctx.send(f"{ctx.author.mention} Source code: {url}")

async def setup(bot):
    await bot.add_cog(AGPL(bot))
    print("AGPL compliance cog loaded — ?source command ready")

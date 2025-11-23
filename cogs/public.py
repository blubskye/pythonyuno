from discord.ext import commands
import discord
import datetime

class Public(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["info", "botinfo"])
    async def bot(self, ctx):
        embed = discord.Embed(title="Yuno", color=0xff003d)
        embed.set_thumbnail(url=ctx.bot.user.display_avatar.url)
        embed.add_field(name="Servers", value=len(self.bot.guilds))
        embed.add_field(name="Users", value=len(self.bot.users))
        embed.add_field(name="discord.py", value=discord.__version__)
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed)

    @commands.command()
    async def invite(self, ctx):
        url = discord.utils.oauth_url(ctx.bot.user.id, permissions=discord.Permissions(8))
        await ctx.send(f"Invite me: {url}")

    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(title="Yuno Commands", color=0xff003d)
        embed.add_field(name="Leveling", value="`?rank [@user]` • `?leaderboard` • `?leveling enable/disable`", inline=False)
        embed.add_field(name="Ranks", value="`?ranks add` • `?ranks remove` • `?ranks list`", inline=False)
        embed.add_field(name="Mod", value="`?clear` • `?ban` • `?kick` • `?unban`", inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Public(bot))

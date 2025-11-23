from discord.ext import commands
import discord

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int = 100):
        amount = min(amount, 1000)
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"Cleared {amount} messages.", delete_after=5)

    @commands.command()
    async def ping(self, ctx):
        await ctx.send(f"Pong! {round(self.bot.latency * 1000)}ms")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        await member.kick(reason=reason)
        await ctx.send(f"{member} has been kicked.")


async def setup(bot):
    await bot.add_cog(Commands(bot))

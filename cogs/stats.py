import discord
from discord.ext import commands
import psutil
import platform
import datetime
import os
import sys
import asyncio

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.process = psutil.Process(os.getpid())
        self.start_time = datetime.datetime.utcnow()

    @commands.command(name="stats", aliases=["status", "info", "botinfo"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def stats(self, ctx):
        uptime = datetime.datetime.utcnow() - self.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        embed = discord.Embed(title="Yuno • System Stats", color=0xff003d, timestamp=discord.utils.utcnow())
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        # Bot info
        embed.add_field(name="Bot", value=f"{self.bot.user.name}#{self.bot.user.discriminator}", inline=True)
        embed.add_field(name="Servers", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="Users", value=len(self.bot.users), inline=True)

        # System
        embed.add_field(name="Python", value=platform.python_version(), inline=True)
        embed.add_field(name="discord.py", value=discord.__version__, inline=True)
        embed.add_field(name="OS", value=platform.system(), inline=True)

        # Performance
        ram = self.process.memory_info().rss / 1024**2
        cpu = self.process.cpu_percent(interval=0.1)
        embed.add_field(name="RAM Usage", value=f"{ram:.1f} MB", inline=True)
        embed.add_field(name="CPU Usage", value=f"{cpu:.1f}%", inline=True)
        embed.add_field(name="Latency", value=f"{self.bot.latency*1000:.0f}ms", inline=True)

        # Uptime
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
        embed.add_field(name="Uptime", value=uptime_str, inline=False)

        # Footer
        embed.set_footer(text="Yuno is alive and watching ♡")

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Stats(bot))
    print("Stats command loaded — transparency achieved.")

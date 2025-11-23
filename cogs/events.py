from discord.ext import commands
import discord

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"┌{'─'*40}┐")
        print(f"│  Yuno is online → {self.bot.user}")
        print(f"│  discord.py {discord.__version__} | Guilds: {len(self.bot.guilds)}")
        print(f"└{'─'*40}┘")
        await self.bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="for levels")
        )

    @commands.Cog.listener()
    async def on_resumed(self):
        print("→ Connection resumed.")

    @commands.Cog.listener()
    async def on_disconnect(self):
        print("→ Disconnected from Discord.")

    # Optional: welcome message when bot joins a server
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        print(f"Joined new guild: {guild.name} ({guild.id}) — {guild.member_count} members")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        print(f"Left guild: {guild.name} ({guild.id})")

async def setup(bot):
    await bot.add_cog(Events(bot))
    print("Events cog loaded")

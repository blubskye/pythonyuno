from discord.ext import commands
import discord
import logging

logger = logging.getLogger(__name__)

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"┌{'─'*40}┐")
        logger.info(f"│  Yuno is online → {self.bot.user}")
        logger.info(f"│  discord.py {discord.__version__} | Guilds: {len(self.bot.guilds)}")
        logger.info(f"└{'─'*40}┘")
        await self.bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="for levels")
        )

    @commands.Cog.listener()
    async def on_resumed(self):
        logger.info("→ Connection resumed.")

    @commands.Cog.listener()
    async def on_disconnect(self):
        logger.warning("→ Disconnected from Discord.")

    # Optional: welcome message when bot joins a server
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        logger.info(f"Joined new guild: {guild.name} ({guild.id}) — {guild.member_count} members")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        logger.info(f"Left guild: {guild.name} ({guild.id})")

async def setup(bot):
    await bot.add_cog(Events(bot))
    logger.info("Events cog loaded")

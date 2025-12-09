import discord
from discord.ext import commands
import os
import asyncio
import logging
from dotenv import load_dotenv
import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    datefmt=config.LOG_DATE_FORMAT,
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)

# Set discord.py logging to WARNING to reduce noise
logging.getLogger('discord').setLevel(logging.WARNING)
logging.getLogger('discord.http').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(
    command_prefix=config.BOT_PREFIX,
    intents=intents,
    case_insensitive=config.BOT_CASE_INSENSITIVE,
    help_command=None,
    description=config.BOT_DESCRIPTION
)

async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                logger.info(f"Loaded cog: {filename[:-3]}")
            except Exception as e:
                logger.error(f"Failed to load cog {filename}: {e}", exc_info=True)

@bot.event
async def on_ready():
    logger.info(f"→ {bot.user} is online | discord.py {discord.__version__}")
    await bot.tree.sync()
    logger.info("→ Slash commands synced")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
